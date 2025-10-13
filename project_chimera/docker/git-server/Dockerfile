FROM alpine:latest

# Install git and openssh
RUN apk add --no-cache git openssh-server

# Create git user
RUN adduser -D -s /bin/sh git

# Set up SSH
RUN ssh-keygen -A
RUN mkdir -p /home/git/.ssh
RUN chown git:git /home/git/.ssh
RUN chmod 700 /home/git/.ssh

# Create git repositories directory
RUN mkdir -p /opt/git
RUN chown git:git /opt/git

# Set up a sample repository
USER git
WORKDIR /opt/git
RUN git init --bare chimera-project.git

USER root
# Copy SSH configuration
COPY sshd_config /etc/ssh/sshd_config

EXPOSE 22

# Start SSH daemon
CMD ["/usr/sbin/sshd", "-D"]
