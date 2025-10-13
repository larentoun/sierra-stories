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

        # ftl supports only a-z
        ftl_entry_name = re.sub(r'[^a-zA-Z0-9]', '-', key).lower()
        ftl_entry_name = re.sub(r'[0]', 'zero', ftl_entry_name)
        ftl_entry_name = re.sub(r'[1]', 'one', ftl_entry_name)
        ftl_entry_name = re.sub(r'[2]', 'two', ftl_entry_name)
        ftl_entry_name = re.sub(r'[3]', 'three', ftl_entry_name)
        ftl_entry_name = re.sub(r'[4]', 'four', ftl_entry_name)
        ftl_entry_name = re.sub(r'[5]', 'five', ftl_entry_name)
        ftl_entry_name = re.sub(r'[6]', 'six', ftl_entry_name)
        ftl_entry_name = re.sub(r'[7]', 'seven', ftl_entry_name)
        ftl_entry_name = re.sub(r'[8]', 'eight', ftl_entry_name)
        ftl_entry_name = re.sub(r'[9]', 'nine', ftl_entry_name)

        while(ftl_entry_name.startswith('-')):
            ftl_entry_name = ftl_entry_name[1:]

        if(ftl_entry_name == ""):
            print(f"Error: Key {key} converts to an empty value!")
            continue

        ftl_lines_ru.append(f"{ftl_entry_name} =")
        ftl_lines_ru.append("{ $case ->")

        for case in cases:
            case_value = value.get(case, "")
            if case_value == "":
                continue
            if case == 'nominative':
                ftl_lines_ru.append(f"  *[{case}]")
                ftl_lines_ru.append("    { $number ->")
                ftl_lines_ru.append(f"      *[one] {value[case]}")
                # TODO: Add support for [one], [few], [many] ?
                ftl_lines_ru.append("    }")

            else:
                ftl_lines_ru.append(f"  [{case}]")
                ftl_lines_ru.append("    { $number ->")
                ftl_lines_ru.append(f"      *[one] {value[case]}")
                ftl_lines_ru.append("    }")

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
