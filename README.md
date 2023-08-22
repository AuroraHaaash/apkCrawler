# apkCrawler
A Crawler For Certain Usage, ONLY For Wandoujia 

基本功能说明
1. 豌豆荚app爬虫，爬取excel中记录的app对应版本apk，以及距离该版本最近的后一个版本apk

2. 绕过认证，但暂未提供自动获取功能，需要手动获取cookie并填入，使用中注意cookie有效时间

3. 下载路径格式：/appSamples/batch_info/appName/...，具体可参考仓库下的示例文件及其中内容

4. app相关信息由lists下文件提供，batch_info为excel文件名

5. 为了保证下载效率，设置了下载的app大小上限为200M，见size_compare()函数

6. 使用中的其他细节请参考代码文件中的注释

功能更新说明
1. 优化pandas对excel读取方式在本使用场景下存在的问题：  
     
    (i)  某app在excel中版本为6，实际版本号为6.00，识别为数字自行去掉了末尾0    
    (ii) beautiful_soup解析时，会优先解析为数字类型而非字符串，如：3.1.3会被解析为字符串，但3.1会优先解析为浮点数

2. 改用流式下载，设置chunk值即可，提高大文件下载速度

3. app文件名检测，防止多次运行时重复下载

4. 防止中文乱码，对应网页源代码中charset设定为固定的值如utf-8而非apparent_encoding

5. 如果同时提供隐私政策下载，则一并下载，并检查
