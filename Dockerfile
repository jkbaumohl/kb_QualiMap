FROM kbase/kbase:sdkbase2.latest
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update

# Here we install a python coverage tool and an
# https library that is out of date in the base image.

RUN pip install coverage

# update security libraries in the base image
RUN pip install cffi --upgrade \
    && pip install pyopenssl --upgrade \
    && pip install ndg-httpsclient --upgrade \
    && pip install pyasn1 --upgrade \
    && pip install requests --upgrade \
    && pip install 'requests[security]' --upgrade

# -----------------------------------------


RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

# install qualimap
# RUN cd /kb/module && \
#    wget https://bitbucket.org/kokonech/qualimap/downloads/qualimap_v2.2.1.zip && \
#    unzip qualimap_v2.2.1.zip && \
#    rm -rf qualimap_v2.2.1.zip && \
#    mv qualimap_v2.2.1 qualimap-bin

# using 2.2.2-dev due to incorrect total reads count
# https://groups.google.com/forum/#!topic/qualimap/boCICeLA_OM
RUN cd /kb/module && \
    wget https://bitbucket.org/kokonech/qualimap/downloads/qualimap-build-26-08-18.tar.gz && \
    tar -xzf qualimap-build-26-08-18.tar.gz && \
    rm -rf qualimap-build-26-08-18.tar.gz && \
    mv qualimap-build-26-08-18 qualimap-bin

# copy in sdk module files
COPY ./ /kb/module
WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
