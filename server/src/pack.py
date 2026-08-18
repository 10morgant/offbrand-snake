from packaging.requirements import Requirement
from packaging.utils import parse_wheel_filename
from packaging.tags import parse_tag

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
tag_str = "rignore-0.7.5-pp39-pypy39_pp73-macosx_11_0_arm64.whl"
name, ver, build, tags = parse_wheel_filename(tag_str)
print(name, ver, build, tags)