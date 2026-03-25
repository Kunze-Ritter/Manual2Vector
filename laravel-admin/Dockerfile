FROM php:8.4-fpm AS app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    unzip \
    libpq-dev \
    libzip-dev \
    libicu-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        pdo_pgsql \
        zip \
        intl \
        gd \
        opcache

# Install Redis extension
RUN pecl install redis \
    && docker-php-ext-enable redis

# Configure Opcache for production
RUN { \
    echo 'opcache.enable=1'; \
    echo 'opcache.memory_consumption=256'; \
    echo 'opcache.interned_strings_buffer=16'; \
    echo 'opcache.max_accelerated_files=20000'; \
    echo 'opcache.validate_timestamps=0'; \
    echo 'opcache.save_comments=1'; \
    echo 'opcache.fast_shutdown=1'; \
} > /usr/local/etc/php/conf.d/opcache.ini

# Configure runtime defaults for HTTP requests and larger document uploads.
RUN { \
    echo 'display_errors=Off'; \
    echo 'display_startup_errors=Off'; \
    echo 'log_errors=On'; \
    echo 'error_reporting=E_ALL'; \
    echo 'upload_max_filesize=100M'; \
    echo 'post_max_size=110M'; \
    echo 'max_execution_time=300'; \
    echo 'max_input_time=300'; \
} > /usr/local/etc/php/conf.d/app-runtime.ini

# Configure PHP-FPM
RUN { \
    echo 'pm = dynamic'; \
    echo 'pm.max_children = 50'; \
    echo 'pm.start_servers = 10'; \
    echo 'pm.min_spare_servers = 5'; \
    echo 'pm.max_spare_servers = 20'; \
    echo 'pm.max_requests = 500'; \
} >> /usr/local/etc/php-fpm.d/www.conf

WORKDIR /var/www/html

# Copy application files
COPY . /var/www/html

# Set permissions for writable directories
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache

# Opcache is tuned for production (validate_timestamps=0). For bind-mounted/local dev,
# mount an override file (e.g., opcache.dev.ini) via a dev compose override to set
# opcache.validate_timestamps=1 so code changes are detected without container restarts.
# Default final stage for PHP-FPM
FROM app
