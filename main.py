while true:
    print("menu")
    print("1 - soma;")
    print("2 - subtração;")
    print("3 - divisão;")
    print("4 - multiplicação;")
    print("5 - potênciação;")
    print("6 - resto;")

    op = int(input("> "))

    if op == 1:
        n1 = float(input("insira o primeiro numero:"))
        n2 = float(input("insira o primeiro numero:"))
        soma = n1 + n2
        print("resultado:  " + str(soma))
    elif op == 2:
        n1 = float(input("insira o primeiro numero:"))
        n2 = float(input("insira o primeiro numero:"))
        subtração = n1 - n2
        print("resultado:  " + str(subtração))
    elif op == 3:
        n1 = float(input("insira o primeiro numero:"))
        n2 = float(input("insira o primeiro numero:"))
        divisão = n1 / n2
        print("resultado:  " + str(divisão))
    elif op == 4:
        n1 = float(input("insira o primeiro numero:"))
        n2 = float(input("insira o primeiro numero:"))
        multiplicação = n1 * n2
        print("resultado:  " + str(multiplicação))
    elif op == 5:
        n1 = float(input("insira o primeiro numero:"))
        n2 = float(input("insira o primeiro numero:"))
        pot = n1 ** n2
        print("resultado:  " + str(pot))
    elif op == 6:
        n1 = float(input("insira o primeiro numero:"))
        n2 = float(input("insira o primeiro numero:"))
        resto = n1 % n2
        print("resultado:  " + str(resto))
    else:
        print("operação invalida")

