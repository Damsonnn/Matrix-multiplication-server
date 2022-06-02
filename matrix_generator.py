import random

size = 100
matrix = ''
for i in range(size * 2):
    for j in range(size - 1):
        matrix += str(random.randint(1, 100)) + ';'
    matrix += str(random.randint(1, 100)) + '\n'

with open('matrix.csv', 'w') as file:
    file.write(matrix)
