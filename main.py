import argparse
import ast
import os
import glob


sample_filename = './sample/sample_input_1.py'

def get_python_files(module_path: str) -> list[ast.ClassDef]:
    python_files = []

    for file_path in glob.glob(os.path.join(module_path, "**/*.py"), recursive=True):
        python_files.append(file_path)
    return python_files


def get_classes(file) -> list[ast.ClassDef]:
    classes = []

    tree = ast.parse(file)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node)

    return classes


def parse_module_classes(module_path: str) -> list[ast.ClassDef]:
    classes = []
    files = get_python_files(module_path)

    for file in files:
        with open(file) as f:
            file_classes = get_classes(f.read())
            classes += file_classes

    return classes


def parse_file_classes(file_path: str) -> list[ast.ClassDef]:
    with open(file_path) as f:
        classes = get_classes(f.read())
    return classes



def calculate_inheritance_factor(not_overriden, total):
    if total == 0:
        return 0
    return round(not_overriden / total, 2)


def calculate_hidding_factor(hidden, total):
    if total == 0:
        return 0
    return round(hidden / total, 2)



def calculate_dit(cls: ast.ClassDef, hierarchy_classes) -> int:
    bases = cls.bases[:]
    while bases:
        base = bases.pop()
        if isinstance(base, ast.Name) and base.id in hierarchy_classes.keys():
            return 1 + \
                calculate_dit(hierarchy_classes[str(
                    base.id)], hierarchy_classes)
    return 0


def calculate_noc(cls: ast.ClassDef, classes: list[ast.ClassDef]) -> int:
    children = []
    for c in classes:
        for b in c.bases:
            if isinstance(b, ast.Name) and cls.name == b.id or \
                    isinstance(b, ast.Attribute) and cls.name == b.attr:
                children.append(c)

    return len(children)


def calculate_mood(cls: ast.ClassDef, hierarchy_classes):
    inherited_methods = set()
    inherited_attributes = set()

    methods = set()
    hidden_methods = set()

    attributes = set()
    hidden_attributes = set()

    for body in cls.body:
        if isinstance(body, ast.FunctionDef):
            if body.name.endswith('_'):
                for attr in body.body:
                    if isinstance(attr, ast.Assign) and isinstance(attr.targets[0], ast.Attribute):
                        value = attr.targets[0].attr
                        attributes.add(value)

                        if value.startswith('__'):
                            hidden_attributes.add(value)

                continue

            methods.add(body.name)

            if body.name.startswith('_'):
                hidden_methods.add(body.name)

        elif isinstance(body, ast.Assign) and isinstance(body.targets[0], ast.Name):
            value = body.targets[0].id
            attributes.add(value)

            if value.startswith('__'):
                hidden_attributes.add(value)

    bases = __iterate_bases(cls, hierarchy_classes)
    for base in bases:
        for body in base.body:
            if isinstance(body, ast.FunctionDef):
                if body.name.startswith('_'):
                    for attr in body.body:
                        if isinstance(attr, ast.Assign) and isinstance(attr.targets[0], ast.Attribute):
                            value = attr.targets[0].attr
                            if not value.startswith('__'):
                                inherited_attributes.add(value)

                    continue

                inherited_methods.add(body.name)

            elif isinstance(body, ast.Assign) and isinstance(body.targets[0], ast.Name):
                value = body.targets[0].id
                if not value.startswith('__'):
                    inherited_attributes.add(value)

    overridden_methods = inherited_methods.intersection(methods)
    methods.update(inherited_methods)

    class_only_attributes = attributes.copy()
    overridden_attributes = inherited_attributes.intersection(attributes)
    attributes.update(inherited_attributes)

    original_methods = [m for m in methods if m not in inherited_methods]

    return {
        'm-total': len(methods),
        'm-hidden': len(hidden_methods),
        'm-not-overriden': len(inherited_methods) - len(overridden_methods),
        'm-overriden': len(overridden_methods),
        'm-original': len(original_methods),
        'a-total': len(attributes),
        'a-hidden': len(hidden_attributes),
        'a-class-only': len(class_only_attributes),
        'a-not-overriden': len(inherited_attributes) - len(overridden_attributes)
    }


def __iterate_bases(cls: ast.ClassDef, hierarchy_classes):
    bases = []
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id in hierarchy_classes.keys():
            bases.append(hierarchy_classes[str(base.id)])
            bases += __iterate_bases(
                hierarchy_classes[str(base.id)], hierarchy_classes)

    return bases


def analyze_metrics(classes: list[ast.ClassDef]):
    hierarchy_classes = {}
    for cls in classes:
        hierarchy_classes[cls.name] = cls

    output = []

    m_total = 0
    m_hidden = 0
    m_overriden = 0
    m_not_overriden = 0
    m_original = 0

    a_total = 0
    a_hidden = 0
    a_original = 0
    a_not_overriden = 0

    for cls in classes:
        dit = calculate_dit(cls, hierarchy_classes)
        noc = calculate_noc(cls, classes)
        mood = calculate_mood(cls, hierarchy_classes)

        m_not_overriden += mood.get('m-not-overriden')
        m_total += mood.get('m-total')
        m_hidden += mood.get('m-hidden')
        m_overriden += mood.get('m-overriden')
        m_original += mood.get('m-original') * noc

        a_total += mood.get('a-total')
        a_hidden += mood.get('a-hidden')
        a_original += mood.get('a-class-only')
        a_not_overriden += mood.get('a-not-overriden')

        mif = calculate_inheritance_factor(
            mood.get('m-not-overriden'), mood.get('m-total'))
        mhf = calculate_hidding_factor(
            mood.get('m-hidden'), mood.get('m-original'))
        ahf = calculate_hidding_factor(
            mood.get('a-hidden'), mood.get('a-class-only'))
        aif = calculate_inheritance_factor(
            mood.get('a-not-overriden'), mood.get('a-total'))
        

        output.append({
            'cls': cls.name,
            'dit': dit,
            'noc': noc,
            'mif': mif,
            'mhf': mhf,
            'aif': aif,
            'ahf': ahf,
        })

    mif = calculate_inheritance_factor(m_not_overriden, m_total)
    mhf = calculate_hidding_factor(m_hidden, m_original)
    ahf = calculate_hidding_factor(a_hidden, a_original)
    aif = calculate_inheritance_factor(a_not_overriden, a_total)

    output.append({
        'cls': "--Total--",
        'mif': mif,
        'mhf': mhf,
        'aif': aif,
        'ahf': ahf,
    })

    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', default=sample_filename, help='File to analyze')
    parser.add_argument('-d', help='Directory to analyze')

    args = parser.parse_args()

    if args.d == None:
        classes = parse_file_classes(args.f)
    else:
        classes = parse_module_classes(args.d)

    output = analyze_metrics(classes)
    with open('output.txt', 'w') as f:
        for o in output:
            for k, v in o.items():
                f.write('%s: %s\n' % (k, v))
            f.write('\n')
