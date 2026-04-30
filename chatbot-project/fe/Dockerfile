FROM nginx:alpine

# Copy custom nginx config template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy all files to html directory
COPY . /usr/share/nginx/html

EXPOSE 80
