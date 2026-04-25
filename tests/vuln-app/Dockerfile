FROM php:8.2-apache

# 意図的にセキュリティ設定を無効化（検証用途専用）
RUN echo "allow_url_fopen = On"       >> /usr/local/etc/php/php.ini && \
    echo "allow_url_include = On"     >> /usr/local/etc/php/php.ini && \
    echo "display_errors = On"        >> /usr/local/etc/php/php.ini && \
    echo "disable_functions ="        >> /usr/local/etc/php/php.ini

RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 \
        libsqlite3-dev \
        netcat-traditional \
    && docker-php-ext-install pdo pdo_sqlite \
    && rm -rf /var/lib/apt/lists/*

# uploadsディレクトリへの書き込みを許可
RUN mkdir -p /var/www/html/uploads && \
    chmod 777 /var/www/html/uploads && \
    chmod 777 /tmp

COPY src/ /var/www/html/

# Apache: mod_rewrite 有効化
RUN a2enmod rewrite
