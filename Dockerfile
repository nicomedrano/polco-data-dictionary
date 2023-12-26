# Fractal Time Tracking Dockerfile 1.0
# (c) Fractal River, LLC

FROM python:3.10.4

# Set the working directory to /app
WORKDIR /workspaces/polco-streamlit-poc

ARG GITHUB_USER
ARG GITHUB_TOKEN

# Get requirements
COPY ./requirements.txt .

# Install the toolkit
RUN apt-get update && apt-get install -y git
RUN pip install git+https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/fractalriver/toolkit.git@v3.0#egg=toolkit[all]

# Install needed packages (requirements.txt), directories and create credentials mount point.
# Please make sure you do NOT put ANY credentials in the image, instead, read them 
# from files in this directory, which will be mounted at runtime.

RUN pip install -r ./requirements.txt

# Copy the code files and shell script to run them
RUN  mkdir ./streamlit-poc
COPY ./streamlit-poc/* /streamlit-poc/


# Run the shell script when the container launches
CMD ["/bin/bash" , "streamlit run main.py"]