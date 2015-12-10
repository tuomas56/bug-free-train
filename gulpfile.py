import gulp

@gulp.task('test')
def task_test():
	from vfs import VFile

	gulp.src('./tests/**/*.py').pipe(VFile.read).pipe(exec)
