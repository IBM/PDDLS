import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name='pddls',
    version='0.2.1',
    # scripts=['pddls'] ,
    scripts=['scripts/pddlsc', 'scripts/pddl2json', 'scripts/json2pddl'] ,
    author="Mich Tatsubori",
    author_email="mich@jp.ibm.com",
    description="PDDLS translator package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibm/pddls",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
 )
