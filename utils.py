def extract_outermost(text):
    # initialize variables
    opening = -1
    closing = -1
    count = 0

    # iterate over the text
    for i, char in enumerate(text):
        if char == '{':
            # count opening braces
            if opening == -1:
                opening = i
            count += 1
        elif char == '}':
            # count closing braces
            count -= 1
            if count == 0:
                closing = i
                break

    if opening != -1 and closing != -1:
        # return the text between the outermost curly braces
        return text[opening + 1: closing]
    else:
        # return None if no outermost curly braces found
        return None
