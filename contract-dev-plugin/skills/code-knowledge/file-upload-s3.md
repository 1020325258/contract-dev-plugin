---
name: file-upload-s3
description: 文件上传 S3 的代码规范，当需要上传文件（pdf、图片等）时，应优先参考此文档。
---

# 文件上传 S3 代码规范
## 上传 S3 得到存在过期时间的文件 url
```java
@Resource 
private S3Service s3Service;

// 1. 生成文件 key，如果是 pdf 后缀为 .pdf；如果是图片，后缀为 .jpg
String fileKey = "file_unique_key" + "_" + UUID.randomUUID() + ".pdf";
// 2. 上传 S3（有效时间默认 15 天）
String fileUrl = s3Service.getMediaUrl(fileKey, 15 * 24 * 60 * 60);
```

## 上传 S3 得到永久的 pdf url
```java
// 引入依赖
@Resource 
private S3Service s3Service;
@Resource
private ContractPdfFileHandleService contractPdfFileHandleService;

// 1. 生成文件 key，如果是 pdf 后缀为 .pdf；如果是图片，后缀为 .jpg
String fileKey = "file_unique_key" + "_" + UUID.randomUUID() + ".pdf";
// 2. 上传 S3（有效时间默认 15 天）
String fileUrl = s3Service.getMediaUrl(fileKey, 15 * 24 * 60 * 60);
// 3. 将 S3 有限过期时间的文件转为永久有效
String tempPath = UUID.randomUUID() + ".pdf";
File file;
try {
    file = contractPdfFileHandleService.downloadFileFromUrl(newPdfS3Url, tempPath);
    String permanentFileUrl = s3Service.uploadPublic(Files.readAllBytes(file.toPath()), key);
    LOGGER.info("永久有效期的 PDF 上传成功, url: {}, tempPath: {}, data: {}, cost: {}ms", permanentFileUrl, tempPath, JSON.toJSONString(data), System.currentTimeMillis() - startTimeMillis);
    return permanentFileUrl;
} catch (IOException e) {
    throw new NrsBusinessException("永久有效期的 PDF 生成失败");
} finally {
    // 删除临时文件
    ContractPdfFileHandleService.cleanUp(Collections.singletonList(tempPath));
}
```