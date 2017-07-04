var gulp = require('gulp'),
    config = require('./package.json'),
    cssnano = require('gulp-cssnano'),
    rename = require('gulp-rename'),
    uglify = require('gulp-uglify'),
    less = require('gulp-less'),
    bower_resolve = require('less-plugin-bower-resolve'),
    util = require('gulp-util'),
    es = require('event-stream');


var pathsConfig = function (appName) {
    this.app = "./" + (appName || config.name);

    return {
        app: this.app,
        templates: this.app + '/templates',
        css: this.app + '/static/css',
        less: this.app + '/static/less',
        fonts: this.app + '/static/fonts',
        images: this.app + '/static/images',
        js: this.app + '/static/js',
    }
};

var paths = pathsConfig();

// Style compilation
gulp.task('styles', function() {
    return es.merge(
        gulp.src(paths.less + '/project.less')
            .pipe(less({
                lint: true,
                plugins: [bower_resolve]
            }))
            .on('error', function (ev) {
                util.beep();
                util.log('LESS error:', ev.message);
            })
            .pipe(gulp.dest(paths.css))
            .pipe(rename({suffix: '.min'}))
            .pipe(cssnano())
            .pipe(gulp.dest(paths.css))
    );
});

// Javascript minification
gulp.task('scripts', function() {
    return gulp.src(paths.js + '/project.js')
        .pipe(uglify())
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(paths.js));
});

// Default task
gulp.task('default', ['styles', 'scripts']);

// Watch
gulp.task('watch', ['default'], function() {
    gulp.watch(paths.less + '/*.less', ['styles']);
    gulp.watch(paths.js + '/*.js', ['scripts']);
});
