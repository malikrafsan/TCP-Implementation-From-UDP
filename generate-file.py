filename = "generate.txt"

file = open(filename, 'w')
str = ""

for i in range(10000):
  str += f"generated file in line {i}\n"

file.write(str)
file.close()
