from lx.project import Project

def read_options(project_path):
    project = Project()
    project.load(project_path)
    project.testOptions()
    project.formatOptions()
    options = project.getOptions()
    return options

if __name__ == "__main__":
    proy = r'test_resources\small_test\small_test-project.lxp'
    options = read_options(proy)
    for k,v in options._data.items():
        print(f'{k:>40} : {v}')