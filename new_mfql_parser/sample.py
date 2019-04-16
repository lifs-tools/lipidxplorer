from mfql_lexer import lexer

if __name__ == '__main__':
    print('Testing the parser')
    print('read mfql')
    with open('sample.mfql','rU') as f:
        mfql = f.read()

    # mfql = [l.strip() for l in mfql]
    # mfql = '\n'.join(mfql)
    print(mfql)
    lexer.input(mfql)

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        print(tok)