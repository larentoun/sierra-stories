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
    ftl_keys = []

    for key, value in data.items():
        cases = ['nominative', 'genitive', 'dative', 'accusative', 'instrumental', 'prepositional', 'gender']

        # .ftl supports only a-zA-Z and -
        # we will use lowercase for letters, uppercase for number string
        ftl_entry_name = value.get('nominative', "")
        ftl_entry_name = re.sub(r'[^a-zA-Z0-9а-яА-Я]', '-', ftl_entry_name).lower()
        ftl_entry_name = cyrillic_to_latin(ftl_entry_name)
        ftl_entry_name = re.sub(r'[0]', 'ZERO', ftl_entry_name)
        ftl_entry_name = re.sub(r'[1]', 'ONE', ftl_entry_name)
        ftl_entry_name = re.sub(r'[2]', 'TWO', ftl_entry_name)
        ftl_entry_name = re.sub(r'[3]', 'THREE', ftl_entry_name)
        ftl_entry_name = re.sub(r'[4]', 'FOUR', ftl_entry_name)
        ftl_entry_name = re.sub(r'[5]', 'FIVE', ftl_entry_name)
        ftl_entry_name = re.sub(r'[6]', 'SIX', ftl_entry_name)
        ftl_entry_name = re.sub(r'[7]', 'SEVEN', ftl_entry_name)
        ftl_entry_name = re.sub(r'[8]', 'EIGHT', ftl_entry_name)
        ftl_entry_name = re.sub(r'[9]', 'NINE', ftl_entry_name)

        while(ftl_entry_name.startswith('-')):
            ftl_entry_name = ftl_entry_name[1:]

        if(ftl_entry_name == ""):
            print(f"Error: Key {key} converts to an empty value!")
            continue

        if(ftl_entry_name in ftl_keys):
            print(f"Error: Duplicate key {ftl_entry_name} detected! Key: {key}")
            continue

        ftl_keys.append(ftl_entry_name)

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

def cyrillic_to_latin(text):
    cyrillic_to_latin_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
    }

    result = ''.join(
        cyrillic_to_latin_map.get(char, char) for char in text
    )

    return result

main()
