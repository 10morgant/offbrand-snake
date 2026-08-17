from packaging.requirements import Requirement

# requires_dist = [
#     'exceptiongroup>=1.0.2; python_version < "3.11"',
#     "idna>=2.8",
#     'typing_extensions>=4.5; python_version < "3.13"',
#     'trio>=0.32.0; extra == "trio"'
# ]
requires_dist = ["exceptiongroup>=1.0.2; python_version < \"3.11\"", "idna>=2.8", "typing_extensions>=4.5; python_version < \"3.13\"", "trio>=0.32.0; extra == \"trio\""]

reqs = [Requirement(r) for r in requires_dist]
a = reqs[0]
b = reqs[1]
c = reqs[2]
d = reqs[3]
print(a)