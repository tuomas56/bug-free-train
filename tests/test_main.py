import gulp_test as gtest

@gtest.test('test')
@gtest.no_errors
def test_test():
	pass

gtest.do_tests()
