import toml
import re

def main():
    toml_file_path = 'input.toml'
    ftl_file_path_ru = 'output_ru.ftl'
    ftl_file_path_en = 'output_en.ftl'

    try:
        with open(toml_file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
    except FileNotFoundError:
        print(f"Error: TOML Input File '{toml_file_path}' not found.")
        return
    except toml.TomlDecodeError:
        print(f"Error: Could not parse TOML Input File '{toml_file_path}'.")
        return

    ftl_lines_ru = []
    ftl_lines_en = []

    for key, value in data.items():
        cases = ['nominative', 'genitive', 'dative', 'accusative', 'instrumental', 'prepositional', 'gender']

        ftl_entry_name = re.sub(r'[^a-zA-Z0-9]', '-', key).lower()
        if ftl_entry_name.startswith('-'):
            ftl_entry_name = ftl_entry_name[1:]

        ftl_lines_ru.append(f"{ftl_entry_name} =")
        ftl_lines_ru.append("{ $case ->")

        for case in cases:
            case_value = value.get(case, "")
            if case_value == "":
                continue
            if case == 'nominative':
                ftl_lines_ru.append(f"  *[{case}] {value[case]}")
            else:
                ftl_lines_ru.append(f"  [{case}] {value[case]}")

        ftl_lines_ru.append("}")
        ftl_lines_ru.append("")

        ftl_lines_en.append(f"{ftl_entry_name} = {key}")

    try:
        with open(ftl_file_path_ru, 'w', encoding='utf-8') as f:
            f.write("\n".join(ftl_lines_ru))
        print(f"Successfully converted '{toml_file_path}' to '{ftl_file_path_ru}'")
    except IOError as e:
        print(f"Error writing to output FTL file '{ftl_file_path_ru}': {e}")

    try:
        with open(ftl_file_path_en, 'w', encoding='utf-8') as f:
            f.write("\n".join(ftl_lines_en))
        print(f"Successfully converted '{toml_file_path}' to '{ftl_file_path_en}'")
    except IOError as e:
        print(f"Error writing to output FTL file '{ftl_file_path_en}': {e}")

main()
