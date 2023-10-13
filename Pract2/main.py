import zipfile
import requests
import io


# Функция для получения зависимостей для указанного пакета
def get_dependencies(package_name):
    dependencies = set()
    response = requests.get(f"https://pypi.org/pypi/{package_name}/json").json()

    # Проверка, существует ли пакет на PyPI
    if "message" in response:
        if response["message"] == "Not Found":
            return dependencies

    version = response["info"]["version"]
    releases = response["releases"]
    last_release = releases[version][0]
    urlWHL = last_release["url"]
    name = urlWHL.split("/")[-1]
    WHLFile = requests.get(urlWHL)
    z = zipfile.ZipFile(io.BytesIO(WHLFile.content))
    metadata = ""
    for zip_name in z.namelist():
        if zip_name.endswith("METADATA"):
            metadata = (str(z.read(zip_name), 'utf-8'))
    lines = metadata.split("\n")

    # Извлечение зависимостей из метаданных
    for line in lines:
        if "Requires-Dist" in str(line):
            dependency = str(line).split(" ")
            if "extra" in dependency:
                break
            dependency = dependency[1]
            dependency = dependency.split("\\")[0]
            dependencies.add(dependency)
    return dependencies


# Функция для форматирования зависимостей в виде вложенных словарей
def format_dependencies_to_nested_dicts(main_package, dependencies):
    dependencies_format = {main_package: []}
    if dependencies is None:
        return dependencies_format
    for dependency in dependencies:
        dependency = dependency.split(" ")
        if dependency == main_package:
            continue
        if not "extra" in dependency:
            package_name = dependency[0]
            internal_dependencies = get_dependencies(package_name)
            internal_dependencies_format = format_dependencies_to_nested_dicts(package_name, internal_dependencies)
            dependencies_format[main_package].append(internal_dependencies_format)
    return dependencies_format


# Функция для конвертации вложенных словарей в код графа
def convertDicts(nested_dicts, depth, i):
    GraphCode = ""
    for key in nested_dicts:
        if not nested_dicts[key]:
            return f"\"{key}\";\n"
        for nested_dict in nested_dicts[key]:
            if i >= depth:
                if i + 1 < depth:
                    return f"\"{key}\"->{convertDicts(nested_dict, depth, i + 1)}"
                else:
                    return f"\"{key}\"\n"
            GraphCode += f"\"{key}\"->{convertDicts(nested_dict, depth, i + 1)}"
    return GraphCode


def main():
    error_message = "Не удалось получить зависимости для указанного пакета"
    while True:
        print("Введите название пакета (0 для выхода): ")
        package_name = input()
        print("Введите глубину: ")
        depth = int(input())
        if package_name == "0":
            break
        elif len(package_name) < 3:
            print(error_message)
        else:
            dependencies = get_dependencies(package_name)
            if dependencies:
                dependency_tree = format_dependencies_to_nested_dicts(package_name, dependencies)
                links = convertDicts(dependency_tree, depth, 0)
                graph_code = "digraph G {\n" + links + "}"
                print(graph_code)
            else:
                print(error_message)


if __name__ == '__main__':
    main_dir = ''
    main()
