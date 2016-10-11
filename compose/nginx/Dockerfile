FROM nginx:latest
ADD nginx.conf /etc/nginx/nginx.conf


ADD start.sh /start.sh
ADD nginx-secure.conf /etc/nginx/nginx-secure.conf
ADD dhparams.pem /etc/ssl/private/dhparams.pem
CMD /start.sh

