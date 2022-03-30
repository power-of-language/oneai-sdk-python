from dataclasses import asdict, dataclass, field
from typing import Dict, List, Type, Union


@dataclass
class Skill:
    '''
    Args:
        api_name: The name of the Skill in the pipeline API.
        is_generator: Whether the Skill is a generator.
        param_fields: Names of the fields of the Skill object that should be passed as parameters to the API.
        label_type: For generator Skills, the field name to give to the output text.
    '''
    api_name: str = ''
    is_generator: bool = False
    _param_fields: List[str] = field(default_factory=list, repr=False, init=False)
    label_type: str = ''
    output_name: str = ''


def skillclass(
    cls: Type=None,
    api_name: str='',
    label_type: str='',
    is_generator: bool=False,
    param_fields: List[str]=[],
    output_name: str = ''
) -> Type[Skill]:
    def wrap(cls):
        if not issubclass(cls, Skill):
            print(f'warning: class {cls.__name__} decorated with @skillclass does not inherit Skill')

        def __init__(self, *args, **kwargs):
            cls_init(self, *args, **kwargs)
            Skill.__init__(self, api_name=api_name, label_type=label_type, is_generator=is_generator, output_name=output_name)
            self._param_fields = param_fields
        
        cls_init = cls.__init__
        cls.__init__ = __init__
        return cls
    
    return wrap if cls is None else wrap(cls)


class Input:
    def __init__(self, type: str):
        self.type = type

    def get_text(self) -> str:
        raise NotImplementedError()

class Document(Input):
    def __init__(self, text: str):
        super().__init__('article')
        self.text = text

    def get_text(self) -> str:
        return self.text

@dataclass
class Utterance:
    speaker: str
    utterance: str

    def __repr__(self):
        return f'{asdict(self)}'

class Conversation(Input):
    def __init__(self, utterances: List[Utterance]=[]):
        super().__init__('conversation')
        self.utterances = utterances

    def get_text(self) -> str:
        return repr(self.utterances)

    @classmethod
    def from_json(cls, json: List[Dict[str, str]]): return cls(
        [Utterance(**utterance) for utterance in json]
    )

    def __repr__(self) -> str:
        return f'oneai.Conversation {repr(self.utterances)}'

@dataclass
class Label:
    type: str = ''
    name: str = ''
    span: List[int] = field(default_factory=lambda: [0, 0])
    value: float = .0

    @classmethod
    def from_json(cls, json): return cls(
        type=json.get('type', ''),
        name=json.get('name', ''),
        span=json.get('span', [0, 0]),
        value=json.get('value', .0)
    )


# @dataclass
# class LabeledText:
#     text: str # todo: this should be an Input
#     labels: List[Label]

#     @classmethod
#     def from_json(cls, json: dict): return cls(
#         text=json['text'],
#         labels=[Label.from_json(l) for l in json['labels']]
#     )


@dataclass
class Output:
    text: str
    skills: List[Skill] # not a dict since Skills are currently mutable & thus unhashable
    data: List[Union[List[Label], 'Output']]

    def __getitem__(self, name: str) -> Union[List[Label], 'Output']:
        return self.__getattr__(name)

    def __getattr__(self, name: str) -> Union[List[Label], 'Output']:
        for i, skill in enumerate(self.skills):
            if (skill.api_name and skill.api_name == name) or \
                (skill.output_name and name in skill.output_name) or \
                (type(skill).__name__ == name):
                return self.data[i]
        raise AttributeError(f'{name} not found in {self}')

    @classmethod
    def build(cls, pipeline, raw_output: Dict, output_index: int=0, skill_index: int=0) -> 'Output':
        if skill_index == 0 and pipeline.steps[0].is_generator:
            return cls(
                text=raw_output['input_text'],
                skills=[pipeline.steps[0]],
                data=[cls.build(pipeline, raw_output, output_index, skill_index + 1)]
            )

        text = raw_output['output'][output_index]['text']
        skills = pipeline.steps[skill_index:]
        labels = [Label.from_json(label) for label in raw_output['output'][output_index]['labels']]
        data = []
        for i, skill in enumerate(skills):
            if skill.is_generator:
                data.append(cls.build(pipeline, raw_output, output_index + 1, skill_index + 1 + i))
            else:
                data.append(list(filter(lambda label: label.type == skill.label_type, labels)))
        return cls(text=text, skills=skills, data=data)

    def __repr__(self) -> str:
        result = f'oneai.Output(text={repr(self.text)}'
        for i, skill in enumerate(self.skills):
            result += f', {skill.api_name}={repr(self.data[i])}'
        return result + ')'
