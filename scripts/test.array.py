"""Test array jobs
"""
import sys


# list variable
array_variables = [f"This is variable {i}" for i in range(10)]

array_i = int(sys.argv[1])


print("*"*60)
print(f"Retrieved from `array_variables`: {array_variables[array_i]}")
print("*"*60)
