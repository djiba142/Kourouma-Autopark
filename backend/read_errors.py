with open('tests_output.log', 'r', encoding='utf-16le') as f:
    text = f.read()
with open('errors_out.txt', 'w', encoding='utf-8') as f:
    f.write(text)
