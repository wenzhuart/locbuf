

locbuf
=======

![](https://img.shields.io/badge/language-python3-orange.svg)
[![LICENSE](https://img.shields.io/badge/license-Anti%20996-blue.svg)](https://github.com/996icu/996.ICU/blob/master/LICENSE)


一个缓存装饰器

- 把从 api 接口返回得到的 pandas.DataFrame 对象缓存为 csv 文件
- 当再次调用该接口时, 使用缓存的数据
- 如果请求的数据大于所缓存的 csv 覆盖范围(以日期判断), 则请求扩展的部份, 并再次缓存

- - -

### 依赖
	
	numpy, pandas

- - -

### 安装

	pip3 install locbuf

- - -

### 导入并实例化

	from locbuf import Locbuf
	buf = Locbuf(tmp_folder='/PATH/TO/TMP', overtime_days=3)
	# or
	buf = Locbuf()

tmp_folder 和 overtime_days 为可选参数<br>
tmp_folder 默认为 '.loc_tmp', 缓存文件的路径<br>
overtime_days 默认为 3, 缓存文件的修改时间大于此值时使用被装饰函数重新请求 api

- - -

### 使用

给需要缓存的函数添加装饰器
	
	@buf.csv_buffer(tag='tag', strt_arg='start', end_arg='end', dfdt_arg='date')

tag: 标识参数, 决定了缓存文件名<br>
strt_arg: 日期参数, 被装饰函数的日期开始参数名<br>
end_arg: 日期参数, 被装饰函数的日期结束参数名<br>
dfdt_arg: 日期参数, api返回的文档中的日期的列名称<br>

(使用日期参数 strt_arg, end_arg, dfdt_arg 时, 三个均不可缺少)<br>
(当没有 tag 参数时, 使用函数名作为缓存文件名)

- - -

### 例:

	class Test():
		"""
		当取得的 df 文档为日期序列形式, 如:
		date 	  | value1 | value2 
		20180101	1	0
		20180102	0	0
		20180103	1	1
		"""
		# 使用日期参数
		@buf.csv_buffer(tag='tag', strt_arg='start', end_arg='end', dfdt_arg='date')
		def get_data_1(self, tag, start=None, end=None):
	    		df = kind_of_api_request(tag=tag, start_date=start, end_date=end)
	    		return df

		"""
		当取得的 df 文档没有日期序列, 如:
		value1 | value2
		1	2
		4	3
		"""
		# 只使用 tag
		@buf.csv_buffer(tag='tag')
		def get_data_2(self, tag, start=None, end=None):
	    		df = kind_of_api_request(tag=tag, start_date=start, end_date=end)
	    		return df

	t = Test()
	t.get_data_1(tag='abc', start='20130101', end='20130109')
	t.get_data_2(tag='abc2')
	

	# 缓存的文件:
	.loc_tmp
	├── get_data_1
	│   └── abc.csv
	└── get_data_2
	    └── abc2.csv
	








