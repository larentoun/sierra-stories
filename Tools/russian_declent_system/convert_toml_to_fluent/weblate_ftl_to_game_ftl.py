from fluent.syntax import parse, serialize
from fluent.syntax.ast import Message, Attribute, Pattern, StringLiteral, Placeable, SelectExpression, VariableReference, TextElement, Resource # Импортируем Resource здесь

def extract_nominative_one_value(parsed_ast, key):
    """
    Извлекает значение из AST по пути: key -> $case -> nominative -> $number -> one.

    Args:
        parsed_ast: Результат парсинга fluent.syntax.parse().
        key (str): Ключ, для которого нужно извлечь значение.

    Returns:
        str or None: Значение из nominative -> one, или None, если не найдено.
    """
    # Найдем сообщение с нужным ключом
    message = None
    for entry in parsed_ast.body:
        if isinstance(entry, Message) and entry.id.name == key:
            message = entry
            break

    if not message:
        print(f"Ключ '{key}' не найден в AST.")
        return None

    # Предполагаем, что значение находится в основном значении сообщения (value)
    if not message.value:
        print(f"У ключа '{key}' нет основного значения.")
        return None

    print(f"  Обработка структуры ключа '{key}':") # Отладка

    # Вложенный обход для поиска $case -> [nominative] -> $number -> *[one]
    def find_nominative_one_in_pattern(pattern, depth=0):
        indent = "    " * (depth + 1) # Для отладочного вывода
        print(f"{indent}Вход в паттерн (глубина {depth})") # Отладка
        for i, element in enumerate(pattern.elements):
            print(f"{indent}  Элемент {i}: {type(element).__name__}") # Отладка
            if isinstance(element, TextElement):
                print(f"{indent}    Текст: '{element.value}'") # Отладка
            elif isinstance(element, Placeable):
                exp = element.expression
                print(f"{indent}    Выражение: {type(exp).__name__}") # Отладка
                if isinstance(exp, SelectExpression):
                    print(f"{indent}      Selector: {type(exp.selector).__name__}") # Отладка
                    if isinstance(exp.selector, VariableReference):
                        print(f"{indent}        Имя переменной: {exp.selector.id.name}") # Отладка (обычно $case или $number)
                    print(f"{indent}      Варианты:") # Отладка
                    for j, variant in enumerate(exp.variants):
                        print(f"{indent}        Вариант {j}: key='{variant.key.name}', default={variant.default}") # Отладка
                        # Проверим, может быть, это [nominative] или *[nominative] (default)
                        if variant.key.name == 'nominative' or (variant.default and hasattr(variant.key, 'name') and variant.key.name == 'nominative'):
                            print(f"{indent}          Найден [nominative] или *[nominative] (default={variant.default}), проверяем внутренний паттерн...") # Отладка
                            # Теперь нужно проверить *внутренний* паттерн этого варианта на наличие $number -> *[one]
                            # Рекурсивный вызов для значения варианта [nominative]
                            inner_result = find_nominative_one_in_pattern(variant.value, depth + 2)
                            if inner_result is not None:
                                print(f"{indent}            Нашли значение внутри [nominative]: '{inner_result}'") # Отладка
                                return inner_result # Нашли, возвращаем
                        else:
                            # Если это не [nominative], проверим его внутренности на случай вложенных Select
                            result = find_nominative_one_in_pattern(variant.value, depth + 2)
                            if result is not None:
                                return result # Нашли, возвращаем
                    # Если мы обработали все варианты текущего SelectExpression и не вернулись,
                    # проверим, может ли *этот* SelectExpression быть $number select (внутри [nominative])
                    # Это может быть, если мы вызвали find_nominative_one_in_pattern из [nominative]
                    # Проверим, есть ли в этом SelectExpression ключ 'one'
                    if any(v.key.name == 'one' for v in exp.variants):
                        print(f"{indent}          Найден $number select (по ключу 'one') на текущем уровне (возможно, внутри [nominative])...") # Отладка
                        for variant in exp.variants:
                            if variant.key.name == 'one' or (variant.default and variant.key.name == 'one'):
                                 # Извлекаем текст из паттерна этого варианта *[one]
                                one_text_elements = [elem.value for elem in variant.value.elements if isinstance(elem, TextElement)]
                                if one_text_elements:
                                    one_value = "".join(one_text_elements).strip()
                                    return one_value # Нашли, возвращаем
                                else:
                                    # Пока вернем None, если нет простого текста
                                    return None
                else:
                    # Если выражение не SelectExpression, проверим его тип
                    # Для полноты обхода можно проверить, является ли exp.placeable
                    # Placeable уже обработан, если exp -- его expression
                    pass
        print(f"{indent}Выход из паттерна (глубина {depth})") # Отладка
        return None # Не нашли

    # Начинаем обход с основного значения сообщения
    extracted_value = find_nominative_one_in_pattern(message.value, depth=0)
    if extracted_value:
        print(f"  Извлечено значение: '{extracted_value}'") # Отладка
        return extracted_value.strip()
    else:
        print(f"  Значение для '{key}' -> nominative -> one не найдено после обхода.")
        return None


def convert_ftl_key_to_value(input_file_path, output_file_path):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input FTL file '{input_file_path}' not found.")
        return
    except IOError as e:
        print(f"Error reading input FTL file '{input_file_path}': {e}")
        return

    try:
        parsed_ast = parse(content)
    except Exception as e:
        print(f"Error parsing FTL file '{input_file_path}': {e}")
        return

    new_entries = []
    new_entries_keys = []
    for entry in parsed_ast.body:
        if isinstance(entry, Message):
            original_key = entry.id.name

            # Извлекаем новое имя ключа
            new_key_name = extract_nominative_one_value(parsed_ast, original_key)

            if new_key_name is None:
                print(f"Пропускаю ключ '{original_key}' из-за отсутствия значения nominative->one.")
                continue

            new_key_name = cyrillic_to_latin(new_key_name)
            if(new_key_name in new_entries_keys):
                print(f"Error: Key {new_key_name} is duplicate!")
                continue

            new_message = Message(
                id=type(entry.id)(name=new_key_name), # Создаем новый Identifier с новым именем
                value=entry.value,
            )

            new_entries.append(new_message)

    new_resource = Resource(body=new_entries)

    try:
        new_content = serialize(new_resource)
    except Exception as e:
        print(f"Error serializing new FTL content: {e}")
        return

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully converted '{input_file_path}' to '{output_file_path}'")
    except IOError as e:
        print(f"Error writing to output FTL file '{output_file_path}': {e}")

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

input_file = 'example_ru.ftl'
output_file = 'output_ru_game_scripted.ftl'
convert_ftl_key_to_value(input_file, output_file)

