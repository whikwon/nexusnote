from setuptools import find_packages, setup

setup(
    name="nexusnote",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
    ],
    author="whikwon",
    author_email="whikwon@gmail.com",
    description="NexusNote Python toolkits",
    url="https://github.com/whikwon/nexusnote",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
