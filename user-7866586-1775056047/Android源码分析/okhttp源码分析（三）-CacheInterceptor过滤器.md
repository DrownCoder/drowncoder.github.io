>1.[okhttp源码分析（一）——基本流程（超详细）](http://www.jianshu.com/p/37e26f4ea57b)
>2.[okhttp源码分析（二）——RetryAndFollowUpInterceptor过滤器](http://www.jianshu.com/p/3b23521f78b6)
>3.[okhttp源码分析（三）——CacheInterceptor过滤器](http://www.jianshu.com/p/bfb13eb3a425)
>4.[okhttp源码分析（四）——ConnectInterceptor过滤器](http://www.jianshu.com/p/4bf4c796db6f)
>5.[okhttp源码分析（五）——CallServerInterceptor过滤器](http://www.jianshu.com/p/4c54e8264971)
### 前言
前一篇博客分析了RetryAndFollowUpInterceptor过滤器，紧接着下一个过滤器应该是BridgeInterceptor，但是这个过滤器的作用主要是在对Request和Resposne的封装，源码理解起来也比较好理解，所以就没有分析这个过滤器。直接分析下一个过滤器CacheInterceptor，其实从名字就可以看出这个过滤器的主要作用就是缓存。
### 分析
#### 1.宏观流程
和上一篇博客的分析相同，按照我的理解，我将过滤器中最关键的方法删减了一下，有助于从宏观上大体对这个过滤器进行理解。
```
@Override public Response intercept(Chain chain) throws IOException {
	//1
    Response cacheCandidate = cache != null
        ? cache.get(chain.request())
        : null;
	//2
    if (networkRequest == null && cacheResponse == null) {
      return new Response;
    }
	//3
    if (networkRequest == null) {
      return cacheResponse;
    }
	//4
      networkResponse = chain.proceed(networkRequest);
	//5
    if (cacheResponse != null) {
      if (networkResponse.code() == HTTP_NOT_MODIFIED) {
        Response response = cacheResponse.newBuilder()
        return response;
      } 
    }
    //6
    Response response = networkResponse;
	//7
    cache.put(response);

    return response;
  }
```
好吧，删了点还是比较多的，但是剩下的代码已经比较直白了，很好理解了。其实看过滤器看多了也基本上掌握了基本法，找最关键的那行代码**chain.proceed(networkRequest);**，上面就是请求前过滤器做的事，下面就是请求后过滤器做的事。
总体上看：
```
//1
Response cacheCandidate = cache != null
        ? cache.get(chain.request())
        : null;
```
1.尝试通过这个Request拿缓存。
```
//2
    if (networkRequest == null && cacheResponse == null) {
      return new Response.code(504);
    }
```
2.如果不允许使用网络并且缓存为空，新建一个504的Resposne返回。
```
//3
    if (networkRequest == null) {
      return cacheResponse;
    }
```
3.如果不允许使用网络，但是有缓存，返回缓存。
```
//4
      networkResponse = chain.proceed(networkRequest);
```
4.链式调用下一个过滤器。
```
//5
    if (cacheResponse != null) {
      if (networkResponse.code() == HTTP_NOT_MODIFIED) {
        Response response = cacheResponse.newBuilder()
        return response;
      } 
    }
```
5.如果缓存不为空，但是网络请求得来的返回码是304（如果返回码是304，客户端有缓冲的文档并发出了一个条件性的请求（一般是提供If-Modified-Since头表示客户只想比指定日期更新的文档）。服务器告诉客户，原来缓冲的文档还可以继续使用。)则使用缓存的响应。
```
//6
    Response response = networkResponse;
	//7
    cache.put(response);

    return response;
```
6、7.使用网络请求得到的Resposne，并且将这个Resposne缓存起来（前提当然是能缓存）。
接下来就是脑袋都大的细节了，我也不敢说分析的十分详细，只能就我的理解总体分析，学习。
#### 2.过程细节
```
@Override public Response intercept(Chain chain) throws IOException {
    //默认cache为null,可以配置cache,不为空尝试获取缓存中的response
    Response cacheCandidate = cache != null
        ? cache.get(chain.request())
        : null;

    long now = System.currentTimeMillis();
    //根据response,time,request创建一个缓存策略，用于判断怎样使用缓存
    CacheStrategy strategy = new CacheStrategy.Factory(now, chain.request(), cacheCandidate).get();
    Request networkRequest = strategy.networkRequest;
    Response cacheResponse = strategy.cacheResponse;

    if (cache != null) {
      cache.trackResponse(strategy);
    }

    if (cacheCandidate != null && cacheResponse == null) {
      closeQuietly(cacheCandidate.body()); // The cache candidate wasn't applicable. Close it.
    }

    // If we're forbidden from using the network and the cache is insufficient, fail.
    //如果缓存策略中禁止使用网络，并且缓存又为空，则构建一个Resposne直接返回，注意返回码=504
    if (networkRequest == null && cacheResponse == null) {
      return new Response.Builder()
          .request(chain.request())
          .protocol(Protocol.HTTP_1_1)
          .code(504)
          .message("Unsatisfiable Request (only-if-cached)")
          .body(Util.EMPTY_RESPONSE)
          .sentRequestAtMillis(-1L)
          .receivedResponseAtMillis(System.currentTimeMillis())
          .build();
    }

    // If we don't need the network, we're done.
    //不使用网络，但是又缓存，直接返回缓存
    if (networkRequest == null) {
      return cacheResponse.newBuilder()
          .cacheResponse(stripBody(cacheResponse))
          .build();
    }

    Response networkResponse = null;
    try {
      //直接走后续过滤器
      networkResponse = chain.proceed(networkRequest);
    } finally {
      // If we're crashing on I/O or otherwise, don't leak the cache body.
      if (networkResponse == null && cacheCandidate != null) {
        closeQuietly(cacheCandidate.body());
      }
    }

    // If we have a cache response too, then we're doing a conditional get.
    //当缓存响应和网络响应同时存在的时候，选择用哪个
    if (cacheResponse != null) {
      if (networkResponse.code() == HTTP_NOT_MODIFIED) {
        //如果返回码是304，客户端有缓冲的文档并发出了一个条件性的请求（一般是提供If-Modified-Since头表示客户
        // 只想比指定日期更新的文档）。服务器告诉客户，原来缓冲的文档还可以继续使用。
        //则使用缓存的响应
        Response response = cacheResponse.newBuilder()
            .headers(combine(cacheResponse.headers(), networkResponse.headers()))
            .sentRequestAtMillis(networkResponse.sentRequestAtMillis())
            .receivedResponseAtMillis(networkResponse.receivedResponseAtMillis())
            .cacheResponse(stripBody(cacheResponse))
            .networkResponse(stripBody(networkResponse))
            .build();
        networkResponse.body().close();

        // Update the cache after combining headers but before stripping the
        // Content-Encoding header (as performed by initContentStream()).
        cache.trackConditionalCacheHit();
        cache.update(cacheResponse, response);
        return response;
      } else {
        closeQuietly(cacheResponse.body());
      }
    }
    //使用网络响应
    Response response = networkResponse.newBuilder()
        .cacheResponse(stripBody(cacheResponse))
        .networkResponse(stripBody(networkResponse))
        .build();
    //所以默认创建的OkHttpClient是没有缓存的
    if (cache != null) {
      //将响应缓存
      if (HttpHeaders.hasBody(response) && CacheStrategy.isCacheable(response, networkRequest)) {
        // Offer this request to the cache.
        //缓存Resposne的Header信息
        CacheRequest cacheRequest = cache.put(response);
        //缓存body
        return cacheWritingResponse(cacheRequest, response);
      }
      //只能缓存GET....不然移除request
      if (HttpMethod.invalidatesCache(networkRequest.method())) {
        try {
          cache.remove(networkRequest);
        } catch (IOException ignored) {
          // The cache cannot be written.
        }
      }
    }

    return response;
  }
```
首先看第一行代码，一开始以为很简单，但看了后才发现里面涉及的流程非常麻烦。
```
Response cacheCandidate = cache != null
        ? cache.get(chain.request())
        : null;
```
从逻辑上看，这里还是比较好理解的，通过Request尝试从缓存成功拿对应的缓存Resposne，如果拿到了则赋值，没有则为null。这里重点就要看怎么取缓存了。其实CacheInterceptor重点比较难以理解的就是：**拿缓存，缓存策略，存缓存**
```
public final class CacheInterceptor implements Interceptor {
  final InternalCache cache;

  public CacheInterceptor(InternalCache cache) {
    this.cache = cache;
  }
}

//======================RealCall.java======================
interceptors.add(new CacheInterceptor(client.internalCache()));
```
首先可以看到这里的cache是InternalCache类型，而且是在构造函数的时候调用的。并且通过RealCall也可以看到，构造这个过滤器的时候传入的是我们构造的OkHttpClient中设置的interanlCache,**而当我们用默认方式构造OkHttpClient的时候是不会创建缓存的，也就是internalCache=null的**
```
public interface InternalCache {
  Response get(Request request) throws IOException;
  CacheRequest put(Response response) throws IOException;
  void remove(Request request) throws IOException;
  void update(Response cached, Response network);
  void trackConditionalCacheHit();

  void trackResponse(CacheStrategy cacheStrategy);
}
```
不出意外，InternalCache是一个接口，OkHttp充分贯彻了**面向接口编程**。接着查找OkHttp中哪个实现了或者说使用了这个接口，对应找到了Cache这个类。
```
public final class Cache implements Closeable, Flushable {
  final InternalCache internalCache = new InternalCache() {
    @Override public Response get(Request request) throws IOException {
      return Cache.this.get(request);
    }
  };

@Nullable Response get(Request request) {
    String key = key(request.url());
    DiskLruCache.Snapshot snapshot;
    Entry entry;
    try {
      snapshot = cache.get(key);
      if (snapshot == null) {
        //没拿到，返回null
        return null;
      }
    } catch (IOException e) {
      // Give up because the cache cannot be read.
      return null;
    }

    try {
      //创建一个Entry,这里其实传入的是CleanFiles数组的第一个（ENTRY_METADATA = 0）得到是头信息,也就是key.0
      entry = new Entry(snapshot.getSource(ENTRY_METADATA));
    } catch (IOException e) {
      Util.closeQuietly(snapshot);
      return null;
    }
    //得到缓存构建得到的response
    Response response = entry.response(snapshot);

    if (!entry.matches(request, response)) {
      Util.closeQuietly(response.body());
      return null;
    }

    return response;
  }
```
可以看到，Cache中实现了InternalCache这个接口，get()方法对应调用的是Cache类中的get方法。所以现在就要看get方法了。
```
String key = key(request.url());
```
首先，通过这行代码我们了解到，缓存的Key是和request的url直接相关的。这里通过url,得到了缓存的key。
```
final DiskLruCache cache;
=============================
DiskLruCache.Snapshot snapshot;
    Entry entry;
    try {
      snapshot = cache.get(key);
      if (snapshot == null) {
        //没拿到，返回null
        return null;
      }
    } catch (IOException e) {
      // Give up because the cache cannot be read.
      return null;
    }
```
下面刚开始看到的时候对各种变量是很难理解的，这里就先不要管，随着后面分析的深入，会理解这里的snapshot变量。可以看到这里得到key后，又会走cache.get()方法，好吧，又要再进入看了。首先要明白，这里的cache对应的类型是DiskLruCache。
```
public synchronized Snapshot get(String key) throws IOException {
    //总结来说就是对journalFile文件的操作，有则删除无用冗余的信息，构建新文件，没有则new一个新的
    initialize();
    //判断是否关闭，如果缓存损坏了，会被关闭
    checkNotClosed();
    //检查key是否满足格式要求，正则表达式
    validateKey(key);
    //获取key对应的entry
    Entry entry = lruEntries.get(key);
    if (entry == null || !entry.readable) return null;
    //获取entry里面的snapshot的值
    Snapshot snapshot = entry.snapshot();
    if (snapshot == null) return null;
    //有则计数器+1
    redundantOpCount++;
    //把这个内容写入文档中
    journalWriter.writeUtf8(READ).writeByte(' ').writeUtf8(key).writeByte('\n');
    //判断是否达清理条件
    if (journalRebuildRequired()) {

      executor.execute(cleanupRunnable);
    }

    return snapshot;
  }
```
进入到DisLruCache内部，首先执行的是```initialize()```方法。
```
public synchronized void initialize() throws IOException {
    //断言，当持有自己锁的时候。继续执行，没有持有锁，直接抛异常
    assert Thread.holdsLock(this);
    //如果初始化过，则直接跳出
    if (initialized) {
      return; // Already initialized.
    }

    // If a bkp file exists, use it instead.
    //如果有journalFileBackup这个文件
    if (fileSystem.exists(journalFileBackup)) {
      // If journal file also exists just delete backup file.
      //如果有journalFile这个文件
      if (fileSystem.exists(journalFile)) {
        //删除journalFileBackup这个文件
        fileSystem.delete(journalFileBackup);
      } else {
        //没有journalFile这个文件，并且有journalFileBackup这个文件，则将journalFileBackup改名为journalFile
        fileSystem.rename(journalFileBackup, journalFile);
      }
    }
    //最后的结果只有两种：1.什么都没有2.有journalFile文件

    // Prefer to pick up where we left off.
    if (fileSystem.exists(journalFile)) {
      //如果有journalFile文件
      try {
        readJournal();
        processJournal();
        //标记初始化完成
        initialized = true;
        return;
      } catch (IOException journalIsCorrupt) {
        Platform.get().log(WARN, "DiskLruCache " + directory + " is corrupt: "
            + journalIsCorrupt.getMessage() + ", removing", journalIsCorrupt);
      }

      // The cache is corrupted, attempt to delete the contents of the directory. This can throw and
      // we'll let that propagate out as it likely means there is a severe filesystem problem.
      try {
        //有缓存损坏导致异常，则删除缓存目录下所有文件
        delete();
      } finally {
        closed = false;
      }
    }
    //如果没有则重新创建一个
    rebuildJournal();
    //标记初始化完成,无论有没有journal文件，initialized都会标记为true，只执行一遍
    initialized = true;
  }
```
总算不用再进入看了，这里assert断言保证这个方法是线程安全的。接着通过对initialized变量来判断，如果初始化过，则直接return。
```
//如果有journalFileBackup这个文件
    if (fileSystem.exists(journalFileBackup)) {
      // If journal file also exists just delete backup file.
      //如果有journalFile这个文件
      if (fileSystem.exists(journalFile)) {
        //删除journalFileBackup这个文件
        fileSystem.delete(journalFileBackup);
      } else {
        //没有journalFile这个文件，并且有journalFileBackup这个文件，则将journalFileBackup改名为journalFile
        fileSystem.rename(journalFileBackup, journalFile);
      }
    }
```
这里首先说明一下**journalFile指的是日志文件，是对缓存一系列操作的记录，不影响缓存的执行流程。**
可以看到这里有两个文件journalFile和journalFileBackup，从名字上可以确定，一个是备份文件，一个是记录文件，随着后面的分析，会发现缓存中充分利用的两个文件，这种形式，一个用于保存，一个用于编辑操作。
这里的判断就很好理解了，如果有journalFileBackup这个文件，并且有journalFile这个文件，则删除journalFileBackup这个没用的文件；如果没有journalFile但是有journalFileBackup这个文件，则将journalFileBackup命名为journalFile。最终可以得出，最后用于保存的其实是journalFile文件。这里执行完后**最后的结果只有两种：1.什么都没有2.有journalFile文件**
```
if (fileSystem.exists(journalFile)) {
      //如果有journalFile文件
      try {
        readJournal();
        processJournal();
        //标记初始化完成
        initialized = true;
        return;
      } catch (IOException journalIsCorrupt) {
        Platform.get().log(WARN, "DiskLruCache " + directory + " is corrupt: "
            + journalIsCorrupt.getMessage() + ", removing", journalIsCorrupt);
      }

      // The cache is corrupted, attempt to delete the contents of the directory. This can throw and
      // we'll let that propagate out as it likely means there is a severe filesystem problem.
      try {
        //有缓存损坏导致异常，则删除缓存目录下所有文件
        delete();
      } finally {
        closed = false;
      }
    }
```
当存在journalFile，执行readJournal(),读取journalFile文件。
```
private void readJournal() throws IOException {
    //利用Okio读取journalFile文件
    BufferedSource source = Okio.buffer(fileSystem.source(journalFile));
    try {
      String magic = source.readUtf8LineStrict();
      String version = source.readUtf8LineStrict();
      String appVersionString = source.readUtf8LineStrict();
      String valueCountString = source.readUtf8LineStrict();
      String blank = source.readUtf8LineStrict();
      //保证和默认值相同
      if (!MAGIC.equals(magic)
          || !VERSION_1.equals(version)
          || !Integer.toString(appVersion).equals(appVersionString)
          || !Integer.toString(valueCount).equals(valueCountString)
          || !"".equals(blank)) {
        throw new IOException("unexpected journal header: [" + magic + ", " + version + ", "
            + valueCountString + ", " + blank + "]");
      }

      int lineCount = 0;
      while (true) {
        try {
          //逐行读取，并根据每行的开头，不同的状态执行不同的操作，主要就是往lruEntries里面add，或者remove
          readJournalLine(source.readUtf8LineStrict());
          lineCount++;
        } catch (EOFException endOfJournal) {
          break;
        }
      }
      //日志操作的记录数=总行数-lruEntries中实际add的行数
      redundantOpCount = lineCount - lruEntries.size();
      //source.exhausted()表示是否还多余字节，如果没有多余字节，返回true，有多余字节返回false
      // If we ended on a truncated line, rebuild the journal before appending to it.
      if (!source.exhausted()) {
        //如果有多余的字节，则重新构建下journal文件
        rebuildJournal();
      } else {
        //获取这个文件的Sink,以便Writer
        journalWriter = newJournalWriter();
      }
    } finally {
      Util.closeQuietly(source);
    }
  }
```
可以看到这里用到了使用OkHttp必须要依赖的库Okio，这个库内部对输入输出流进行了很多优化，分帧读取写入，帧还有池的概念，具体原理可以网上去学习。
```
String magic = source.readUtf8LineStrict();
      String version = source.readUtf8LineStrict();
      String appVersionString = source.readUtf8LineStrict();
      String valueCountString = source.readUtf8LineStrict();
      String blank = source.readUtf8LineStrict();
      //保证和默认值相同
      if (!MAGIC.equals(magic)
          || !VERSION_1.equals(version)
          || !Integer.toString(appVersion).equals(appVersionString)
          || !Integer.toString(valueCount).equals(valueCountString)
          || !"".equals(blank)) {
        throw new IOException("unexpected journal header: [" + magic + ", " + version + ", "
            + valueCountString + ", " + blank + "]");
      }
```
这里利用Okio读取journalFile，前面主要是**逐行读取**一些参数，进行校验，保证这些参数的正确性。
```
int lineCount = 0;
      while (true) {
        try {
          //逐行读取，并根据每行的开头，不同的状态执行不同的操作，主要就是往lruEntries里面add，或者remove
          readJournalLine(source.readUtf8LineStrict());
          lineCount++;
        } catch (EOFException endOfJournal) {
          break;
        }
      }
```
校验成功了，就进行逐行读取，所以这里需要看一下readJournalLine()方法。
```
private void readJournalLine(String line) throws IOException {
    //记录第一个空串的位置
    int firstSpace = line.indexOf(' ');
    if (firstSpace == -1) {
      throw new IOException("unexpected journal line: " + line);
    }

    int keyBegin = firstSpace + 1;
    //记录第二个空串的位置
    int secondSpace = line.indexOf(' ', keyBegin);
    final String key;
    if (secondSpace == -1) {
      //如果中间没有空串，则直接截取得到key
      key = line.substring(keyBegin);
      //如果解析出来的是"REMOVE skjdglajslkgjl"这样以REMOVE开头
      if (firstSpace == REMOVE.length() && line.startsWith(REMOVE)) {
        //移除这个key，lruEntries是LinkedHashMap
        lruEntries.remove(key);
        return;
      }
    } else {
      //解析两个空格间的字符串为key
      key = line.substring(keyBegin, secondSpace);
    }
    //取出Entry对象
    Entry entry = lruEntries.get(key);
    //如果Enty对象为null
    if (entry == null) {
      //new一个Entry，put进去
      entry = new Entry(key);
      lruEntries.put(key, entry);
    }
    //如果是“CLEAN 1 2”这样的以CLAEN开头
    if (secondSpace != -1 && firstSpace == CLEAN.length() && line.startsWith(CLEAN)) {
      //取第二个空格后面的字符串，parts变成[1,2]
      String[] parts = line.substring(secondSpace + 1).split(" ");
      //可读
      entry.readable = true;
      //不被编辑
      entry.currentEditor = null;
      //设置长度
      entry.setLengths(parts);
    } else if (secondSpace == -1 && firstSpace == DIRTY.length() && line.startsWith(DIRTY)) {
      //如果是“DIRTY lskdjfkl”这样以DIRTY开头，新建一个Editor
      entry.currentEditor = new Editor(entry);
    } else if (secondSpace == -1 && firstSpace == READ.length() && line.startsWith(READ)) {
      //如果是“READ slkjl”这样以READ开头，不需要做什么事
      // This work was already done by calling lruEntries.get().
    } else {
      throw new IOException("unexpected journal line: " + line);
    }
  }
```
这里一开始可能比较难以理解，说明一下journalFile每一行的保存格式是这样的：**REMOVE sdkjlg 2341 1234**
第一个空格前面代表这条日志的操作内容，后面的第一个个保存的是key，后面这两个内容根据前面的操作存入缓存内容对应的length...
```
if (secondSpace == -1) {
      //如果中间没有空串，则直接截取得到key
      key = line.substring(keyBegin);
      //如果解析出来的是"REMOVE skjdglajslkgjl"这样以REMOVE开头
      if (firstSpace == REMOVE.length() && line.startsWith(REMOVE)) {
        //移除这个key，lruEntries是LinkedHashMap
        lruEntries.remove(key);
        return;
      }
    } else {
      //解析两个空格间的字符串为key
      key = line.substring(keyBegin, secondSpace);
    }
```
如果没有第二个空格，那么数据格式就是这样的**REMOVE skjdglajslkgjl**
截取第一个空格后面的内容作为key，如果是以REMOVE开头，则从lruEntries中移除这个key对应的缓存。
```
final LinkedHashMap<String, Entry> lruEntries = new LinkedHashMap<>(0, 0.75f, true);
```
这里说明一下，使用一个LinkedHashMap保存的。
如果有第二个空格，则还是去第一个和第二个空格之间的内容当做key。
```
//取出Entry对象
    Entry entry = lruEntries.get(key);
    //如果Enty对象为null
    if (entry == null) {
      //new一个Entry，put进去
      entry = new Entry(key);
      lruEntries.put(key, entry);
    }
```
并且尝试取这个key对应的Entry,如果没有，则new一个put进入。
```
//如果是“CLEAN jklldsg 2 5”这样的以CLAEN开头
    if (secondSpace != -1 && firstSpace == CLEAN.length() && line.startsWith(CLEAN)) {
      //取第二个空格后面的字符串，parts变成[1,2]
      String[] parts = line.substring(secondSpace + 1).split(" ");
      //可读
      entry.readable = true;
      //不被编辑
      entry.currentEditor = null;
      //设置长度
      entry.setLengths(parts);
    }
```
**CLEAN jklldsg 2 5**如果是以CLEAN开头的话，则将取出key后面的数组，设置可读，不可编辑，设置entry的长度。这里先说明一下Entry类。
```
private final class Entry {
    final String key;

    /** Lengths of this entry's files. */
    final long[] lengths;
    //用于保存持久数据，作用是读取 最后的格式：key.0
    final File[] cleanFiles;
    //用于保存编辑的临时数据，作用是写，最后的格式：key.0.tmp
    final File[] dirtyFiles;
}
```
我的理解是，Entry中有两个数组，cleanFile是用于保存持久性数据，用于读取，dirtyFiles是用于进行编辑，当编辑完成后会执行commit操作，将dirtyFile赋值给cleanFile。length适用于保存Entry中每个数组对应的file的数量。
所以当**CLEAN jklldsg 2 5**如果是以CLEAN开头的话，cleanFiles对应的size就是2，dirtyFiles对应的数量是5（默认都是2个）

```
else if (secondSpace == -1 && firstSpace == DIRTY.length() && line.startsWith(DIRTY)) {
      //如果是“DIRTY lskdjfkl”这样以DIRTY开头，新建一个Editor
      entry.currentEditor = new Editor(entry);
    } else if (secondSpace == -1 && firstSpace == READ.length() && line.startsWith(READ)) {
      //如果是“READ slkjl”这样以READ开头，不需要做什么事
      // This work was already done by calling lruEntries.get().
    } else {
      throw new IOException("unexpected journal line: " + line);
    }
```
上面理解了，后面其实也就对应很好理解了，如果是以DIRTY开头，则新建一个Editor表示这个Entry可以编辑。如果是READ开头，则不需要做任何事。
到此结束了对**readJournalLine()**方法的分析，总结一下这个方法的作用：**逐行读取，并根据每行的开头，不同的状态执行不同的操作，主要就是往lruEntries里面add，或者remove。接着返回到**readJournal()**方法中。**
```
while (true) {
        try {
          //逐行读取，并根据每行的开头，不同的状态执行不同的操作，主要就是往lruEntries里面add，或者remove
          readJournalLine(source.readUtf8LineStrict());
          lineCount++;
        } catch (EOFException endOfJournal) {
          break;
        }
      }
```
可以看到这里，利用lineCount记录读取的行数。
```
//日志中操作的记录数=总行数-lruEntries中实际add的行数
      redundantOpCount = lineCount - lruEntries.size();
      //source.exhausted()表示是否还多余字节，如果没有多余字节，返回true，有多余字节返回false
      // If we ended on a truncated line, rebuild the journal before appending to it.
      if (!source.exhausted()) {
        //如果有多余的字节，则重新构建下journal文件
        rebuildJournal();
      } else {
        //获取这个文件的Sink,以便Writer
        journalWriter = newJournalWriter();
      }
```
读取完毕后会计算日志中操作的记录数，日志中操作的记录数=读取的总行数-lruEntries中实际保存的行数。
接下来source.exhausted()是表示是否还多余字节，如果没有多余字节，返回true，有多余字节返回false，如果有多余的字节则需要执行rebuildJournal()，没有则获得这个文件的Sink，用于Write操作。
```
synchronized void rebuildJournal() throws IOException {
    if (journalWriter != null) {
      journalWriter.close();
    }

    BufferedSink writer = Okio.buffer(fileSystem.sink(journalFileTmp));
    try {
      //写入校验信息
      writer.writeUtf8(MAGIC).writeByte('\n');
      writer.writeUtf8(VERSION_1).writeByte('\n');
      writer.writeDecimalLong(appVersion).writeByte('\n');
      writer.writeDecimalLong(valueCount).writeByte('\n');
      writer.writeByte('\n');
      //利用刚才逐行读的内容按照格式重新构建
      for (Entry entry : lruEntries.values()) {
        if (entry.currentEditor != null) {
          writer.writeUtf8(DIRTY).writeByte(' ');
          writer.writeUtf8(entry.key);
          writer.writeByte('\n');
        } else {
          writer.writeUtf8(CLEAN).writeByte(' ');
          writer.writeUtf8(entry.key);
          entry.writeLengths(writer);
          writer.writeByte('\n');
        }
      }
    } finally {
      writer.close();
    }
    //用新构建的journalFileTmp替换当前的journalFile文件
    if (fileSystem.exists(journalFile)) {
      fileSystem.rename(journalFile, journalFileBackup);
    }
    fileSystem.rename(journalFileTmp, journalFile);
    fileSystem.delete(journalFileBackup);

    journalWriter = newJournalWriter();
    hasJournalErrors = false;
    mostRecentRebuildFailed = false;
  }
```
可以看到这里主要是将lruEntries中保存的内容逐行写成一个journalFileTmp，将新构建的journalFileTmp替换当前包含冗余信息的journalFile文件，达到重新构建的效果。
到这里**readJournal()**方法分析完了，总结下这个方法的作用：**主要是读取journalFile，根据日志文件中的日志信息，过滤无用冗余的信息，有冗余的则重新构建，最后保证journalFile日志文件没有冗余信息。**

执行完readJournal()方法，回到initialize（)方法中。
```
	try {
        readJournal();
        processJournal();
        //标记初始化完成
        initialized = true;
        return;
      } catch (IOException journalIsCorrupt) {
        Platform.get().log(WARN, "DiskLruCache " + directory + " is corrupt: "
            + journalIsCorrupt.getMessage() + ", removing", journalIsCorrupt);
      }
```
这里需要看一下processJournal()方法
```
private void processJournal() throws IOException {
    //删除journalFileTmp文件
    fileSystem.delete(journalFileTmp);
    for (Iterator<Entry> i = lruEntries.values().iterator(); i.hasNext(); ) {
      Entry entry = i.next();
      if (entry.currentEditor == null) {
        //表明数据是CLEAN,循环记录SIZE
        for (int t = 0; t < valueCount; t++) {
          size += entry.lengths[t];
        }
      } else {
        //表明数据是DIRTY，删除
        entry.currentEditor = null;
        for (int t = 0; t < valueCount; t++) {
          fileSystem.delete(entry.cleanFiles[t]);
          fileSystem.delete(entry.dirtyFiles[t]);
        }
        //移除Entry
        i.remove();
      }
    }
  }
```
可以看到，这里删除了刚才创建的journalFileTmp文件，并且遍历lruEntries，记录不可编辑的数据长度size(也就是CLEAN),删除DIRTY数据，也就是只保留CLEAN持久性数据，删除编辑的数据。
```
	try {
        readJournal();
        processJournal();
        //标记初始化完成
        initialized = true;
        return;
      } catch (IOException journalIsCorrupt) {
        Platform.get().log(WARN, "DiskLruCache " + directory + " is corrupt: "
            + journalIsCorrupt.getMessage() + ", removing", journalIsCorrupt);
      }
```
可以看到到这里，接下来的就是将initialized标记为true，表示初始化完成。到这里其实initialize已经完成了，继续看initialize()方法。
后面就比较简单了，当没有journalFile，则会调用我们刚才分析过的方法rebuildJournal()重新创建一个日志文件，仍然将initialized标记为true,说明无论有没有journal文件，initialized都会标记为true，只执行一遍。
到这里总算将initialize()分析完了，这里总结一下这个方法：
>1.这个方法线程安全
>2.如果初始化过了，则什么都不干，只初始化一遍
>3.如果有journalFile日志文件，则对journalFile文件和lruEntries进行初始化操作，主要是删除冗余信息，和DIRTY信息。
>4.没有则构建一个journalFile文件。

到这initialize()方法总算分析完了，接下来回到get()方法中，剩下的其实就容易点了。
接下来这些都没有什么重要的地方，我注释都写的很清楚，总结一下get()方法的主要操作：
>1.初始化日志文件和lruEntries
>2.检查保证key正确后获取缓存中保存的Entry。
>3.操作计数器+1
>4.往日志文件中写入这次的READ操作。
>5.根据redundantOpCount判断是否需要清理日志信息。
>6.需要则开启线程清理。
>7.不需要则返回缓存。

这里看一下两个地方，第一个journalRebuildRequired()用于判断是否需要清理缓存。
```
boolean journalRebuildRequired() {
    final int redundantOpCompactThreshold = 2000;
    //清理的条件是当前redundantOpCount大于2000，并且redundantOpCount的值大于linkedList里面的size
    return redundantOpCount >= redundantOpCompactThreshold
        && redundantOpCount >= lruEntries.size();
  }
```
可以看到清理的条件是当前redundantOpCount大于2000，并且redundantOpCount的值大于linkedList里面的size。
下面一个需要看的地方就是清理线程cleanupRunnable。
```
private final Runnable cleanupRunnable = new Runnable() {
    public void run() {
      synchronized (DiskLruCache.this) {
        //如果没有初始化或者已经关闭了，则不需要清理，这里注意|和||的区别，|会两个条件都检查
        if (!initialized | closed) {
          return; // Nothing to do
        }

        try {
		  //清理
          trimToSize();
        } catch (IOException ignored) {
          mostRecentTrimFailed = true;
        }

        try {
          if (journalRebuildRequired()) {
            //如果还要清理，重新构建
            rebuildJournal();
            //计数器置0
            redundantOpCount = 0;
          }
        } catch (IOException e) {
          //如果抛异常了，设置最近的一次构建失败
          mostRecentRebuildFailed = true;
          journalWriter = Okio.buffer(Okio.blackhole());
        }
      }
    }
  };
```
这里先总结一下这里的操作流程：
>1.如果还没有初始化或者缓存关闭了，则不清理。
>2.执行清理操作。
>3.如果清理完了还是判断后还需要清理，只能重新构建日志文件，并且日志记录器记0。

这里主要就需要看一下清理操作trimToSize()
```
void trimToSize() throws IOException {
    //遍历直到满足大小
    while (size > maxSize) {
      Entry toEvict = lruEntries.values().iterator().next();
      removeEntry(toEvict);
    }
    mostRecentTrimFailed = false;
  }
```
可以看到这里就是一个遍历，知道满足maxSize条件，这里的maxSize是可以设置的。
```
boolean removeEntry(Entry entry) throws IOException {
    if (entry.currentEditor != null) {
      //结束editor
      entry.currentEditor.detach(); // Prevent the edit from completing normally.
    }

    for (int i = 0; i < valueCount; i++) {
      //清除用于保存文件的cleanFiles
      fileSystem.delete(entry.cleanFiles[i]);
      size -= entry.lengths[i];
      entry.lengths[i] = 0;
    }
    //计数器加1
    redundantOpCount++;
    //增加一条删除日志
    journalWriter.writeUtf8(REMOVE).writeByte(' ').writeUtf8(entry.key).writeByte('\n');
    //移除entry
    lruEntries.remove(entry.key);
    //如果需要重新清理一下，边界情况
    if (journalRebuildRequired()) {
      //清理
      executor.execute(cleanupRunnable);
    }

    return true;
  }
```
这里的执行流程：
>1.停止编辑操作
>2.清楚用于保存的cleanFiles
>3.增加一条清楚日志记录，计数器+1
>4.移除对应key的entry
>5.由于增加了一条日志，判断是否需要清理，不然可能会越清越多...

至此，get()方法终于分析完成了，接着就要返回Cache中的get()方法继续看。
```
@Nullable Response get(Request request) {
    String key = key(request.url());
    DiskLruCache.Snapshot snapshot;
    Entry entry;
    try {
      snapshot = cache.get(key);
      if (snapshot == null) {
        //没拿到，返回null
        return null;
      }
    } catch (IOException e) {
      // Give up because the cache cannot be read.
      return null;
    }

    try {
      //创建一个Entry,这里其实传入的是CleanFiles数组的第一个（ENTRY_METADATA = 0）得到是头信息,也就是key.0
      entry = new Entry(snapshot.getSource(ENTRY_METADATA));
    } catch (IOException e) {
      Util.closeQuietly(snapshot);
      return null;
    }
    //得到缓存构建得到的response
    Response response = entry.response(snapshot);

    if (!entry.matches(request, response)) {
      Util.closeQuietly(response.body());
      return null;
    }

    return response;
  }
```
这里一样，先总结一下get(）方法的具体流程。
>1.通过执行DiskLruCache的get方法拿到snapshot信息。
>2.通过拿到的snapshot信息，取cleanFiles[0]中保存的头信息，构建头相关的信息的Entry.
>3.通过snapshot中的cleanFiles[1]构建body信息，最终构建成缓存中保存的Response。
>4.返回缓存中保存的Resposne。

可以看到这里的重点是先构建header，再构建body，最后组合成Resposne。对应的两个流程这里分析一下，
```
try {
      //创建一个Entry,这里其实传入的是CleanFiles数组的第一个（ENTRY_METADATA = 0）得到是头信息,也就是key.0
      entry = new Entry(snapshot.getSource(ENTRY_METADATA));
    } catch (IOException e) {
      Util.closeQuietly(snapshot);
      return null;
    }
```
可以看到，这里通过得到的snapshot.getSource构建了Entry（这个Entry是Cache的内部类，不是DiskLruCache的内部类）。**这里注意一个地方，这里的ENTRY_METADATA = 0。**
```
public final class Snapshot implements Closeable {
    private final String key;
    private final long sequenceNumber;
    private final Source[] sources;
    private final long[] lengths;

    Snapshot(String key, long sequenceNumber, Source[] sources, long[] lengths) {
      this.key = key;
      this.sequenceNumber = sequenceNumber;
      this.sources = sources;
      this.lengths = lengths;
    }
	public Source getSource(int index) {
      return sources[index];
    }
}
```
可以看到这里的getSource其实就是返回Source数组中的元素，而Source数组是在Snapshot的构造函数的时候赋值，所以对应的可以找构造Snapshot的地方。
```
Snapshot snapshot() {
      if (!Thread.holdsLock(DiskLruCache.this)) throw new AssertionError();

      Source[] sources = new Source[valueCount];
      long[] lengths = this.lengths.clone(); // Defensive copy since these can be zeroed out.
      try {
        for (int i = 0; i < valueCount; i++) {
          //可以看到这里其实是将cleanFiles传给了sources
          sources[i] = fileSystem.source(cleanFiles[i]);
        }
        return new Snapshot(key, sequenceNumber, sources, lengths);
      } catch (FileNotFoundException e) {
        // A file must have been deleted manually!
        for (int i = 0; i < valueCount; i++) {
          if (sources[i] != null) {
            Util.closeQuietly(sources[i]);
          } else {
            break;
          }
        }
        // Since the entry is no longer valid, remove it so the metadata is accurate (i.e. the cache
        // size.)
        try {
          removeEntry(this);
        } catch (IOException ignored) {
        }
        return null;
      }
    }
```
看到这个方法，其实应该注意到这个就是我们在调用DiskLruCache中的get()方法时最后返回Snapshot调用的方法,具体下方代码贴出了，这时候可以看到source数组其实是将entry中的cleanfile数组对应的保存到source数组中，**这也验证了我们前面说的clean数组是用来保存持久性数据，也就是真正用来存东西的地方**，而且记得前面提到ENTRY_METADATA = 0，所以对应的取的也是clean数组中的第一个文件，**也验证了前面说的clean数组分两部分，第一部分保存头，第二部分保存body**
```
public synchronized Snapshot get(String key) throws IOException {
    ...
    Snapshot snapshot = entry.snapshot();
    ...
  }
```
getSource看完了，这时候来看一下Cache中Entry这个内部类，**注意不是DiskLruCache中的Entry**
```
Entry(Source in) throws IOException {
      try {
        BufferedSource source = Okio.buffer(in);
        url = source.readUtf8LineStrict();
        requestMethod = source.readUtf8LineStrict();
        //得到cleanfiles[0]来构建头信息
        Headers.Builder varyHeadersBuilder = new Headers.Builder();
        int varyRequestHeaderLineCount = readInt(source);
        for (int i = 0; i < varyRequestHeaderLineCount; i++) {
          varyHeadersBuilder.addLenient(source.readUtf8LineStrict());
        }
        varyHeaders = varyHeadersBuilder.build();

        StatusLine statusLine = StatusLine.parse(source.readUtf8LineStrict());
        protocol = statusLine.protocol;
        code = statusLine.code;
        message = statusLine.message;
        Headers.Builder responseHeadersBuilder = new Headers.Builder();
        int responseHeaderLineCount = readInt(source);
        for (int i = 0; i < responseHeaderLineCount; i++) {
          responseHeadersBuilder.addLenient(source.readUtf8LineStrict());
        }
        String sendRequestMillisString = responseHeadersBuilder.get(SENT_MILLIS);
        String receivedResponseMillisString = responseHeadersBuilder.get(RECEIVED_MILLIS);
        responseHeadersBuilder.removeAll(SENT_MILLIS);
        responseHeadersBuilder.removeAll(RECEIVED_MILLIS);
        sentRequestMillis = sendRequestMillisString != null
            ? Long.parseLong(sendRequestMillisString)
            : 0L;
        receivedResponseMillis = receivedResponseMillisString != null
            ? Long.parseLong(receivedResponseMillisString)
            : 0L;
		//构建了header
        responseHeaders = responseHeadersBuilder.build();

        if (isHttps()) {
          String blank = source.readUtf8LineStrict();
          if (blank.length() > 0) {
            throw new IOException("expected \"\" but was \"" + blank + "\"");
          }
          String cipherSuiteString = source.readUtf8LineStrict();
          CipherSuite cipherSuite = CipherSuite.forJavaName(cipherSuiteString);
          List<Certificate> peerCertificates = readCertificateList(source);
          List<Certificate> localCertificates = readCertificateList(source);
          TlsVersion tlsVersion = !source.exhausted()
              ? TlsVersion.forJavaName(source.readUtf8LineStrict())
              : TlsVersion.SSL_3_0;
          handshake = Handshake.get(tlsVersion, cipherSuite, peerCertificates, localCertificates);
        } else {
          handshake = null;
        }
      } finally {
        in.close();
      }
    }
```
这里通过Entry的构造方法更能说明clean数组中的第一项是用来保存header信息的，从代码中可以看到利用Header.builder对传入进来的Source(也就是clean[0])进行构建，最后利用build()方法构建了header信息。

头构建完了，现在就需要找构建body的地方，因为剩下的代码只剩下
```
//得到缓存构建得到的response
    Response response = entry.response(snapshot);

//Entry内部类
public Response response(DiskLruCache.Snapshot snapshot) {
      String contentType = responseHeaders.get("Content-Type");
      String contentLength = responseHeaders.get("Content-Length");
      Request cacheRequest = new Request.Builder()
          .url(url)
          .method(requestMethod, null)
          .headers(varyHeaders)
          .build();
      return new Response.Builder()
          .request(cacheRequest)
          .protocol(protocol)
          .code(code)
          .message(message)
          .headers(responseHeaders)
          .body(new CacheResponseBody(snapshot, contentType, contentLength))
          .handshake(handshake)
          .sentRequestAtMillis(sentRequestMillis)
          .receivedResponseAtMillis(receivedResponseMillis)
          .build();
    }
```
大体上一看，这个方法的作用基本上就是利用Resposne.builder构建缓存中的Resposne了，但是没有找到明显的写入Body的地方，唯一由body的就是
```.body(new CacheResponseBody(snapshot, contentType, contentLength))```,所以只能进入CacheResponseBody的构造函数中。
```
CacheResponseBody(final DiskLruCache.Snapshot snapshot,
        String contentType, String contentLength) {
      this.snapshot = snapshot;
      this.contentType = contentType;
      this.contentLength = contentLength;
      //这里ENTRY_BODY=1，同样拿的是CleanFiles数组，构建Responsebody
      Source source = snapshot.getSource(ENTRY_BODY);
      bodySource = Okio.buffer(new ForwardingSource(source) {
        @Override public void close() throws IOException {
          snapshot.close();
          super.close();
        }
      });
    }
```
可以看到终于发现了和刚才Header一样的代码，这里ENTRY_BODY=1，对应的还是取source数组中的下标为1的地方，构建body。**到现在可以看出来，clean数组的0对应保存的Header信息，1对应保存的BODY信息。**

**这里分析完构建header和body得到对应的缓存的Resposne后，对应非常长长长的从缓存中拿缓存的Resposne流程终于结束。**
其实到这里，缓存的主要思想其实已经理解大概了后面的的其实就比较好理解了。这里get()方法结束了，也终于要回到CacheInterceptor的主要方法中了。这里再放一遍代码，因为翻上去太长了。。。
```
@Override public Response intercept(Chain chain) throws IOException {
    //默认cache为null,可以配置cache,不为空尝试获取缓存中的response
    Response cacheCandidate = cache != null
        ? cache.get(chain.request())
        : null;

    long now = System.currentTimeMillis();
    //根据response,time,request创建一个缓存策略，用于判断怎样使用缓存
    CacheStrategy strategy = new CacheStrategy.Factory(now, chain.request(), cacheCandidate).get();
    Request networkRequest = strategy.networkRequest;
    Response cacheResponse = strategy.cacheResponse;

    if (cache != null) {
      cache.trackResponse(strategy);
    }

    if (cacheCandidate != null && cacheResponse == null) {
      closeQuietly(cacheCandidate.body()); // The cache candidate wasn't applicable. Close it.
    }

    // If we're forbidden from using the network and the cache is insufficient, fail.
    //如果缓存策略中禁止使用网络，并且缓存又为空，则构建一个Resposne直接返回，注意返回码=504
    if (networkRequest == null && cacheResponse == null) {
      return new Response.Builder()
          .request(chain.request())
          .protocol(Protocol.HTTP_1_1)
          .code(504)
          .message("Unsatisfiable Request (only-if-cached)")
          .body(Util.EMPTY_RESPONSE)
          .sentRequestAtMillis(-1L)
          .receivedResponseAtMillis(System.currentTimeMillis())
          .build();
    }

    // If we don't need the network, we're done.
    //不使用网络，但是又缓存，直接返回缓存
    if (networkRequest == null) {
      return cacheResponse.newBuilder()
          .cacheResponse(stripBody(cacheResponse))
          .build();
    }

    Response networkResponse = null;
    try {
      //直接走后续过滤器
      networkResponse = chain.proceed(networkRequest);
    } finally {
      // If we're crashing on I/O or otherwise, don't leak the cache body.
      if (networkResponse == null && cacheCandidate != null) {
        closeQuietly(cacheCandidate.body());
      }
    }

    // If we have a cache response too, then we're doing a conditional get.
    //当缓存响应和网络响应同时存在的时候，选择用哪个
    if (cacheResponse != null) {
      if (networkResponse.code() == HTTP_NOT_MODIFIED) {
        //如果返回码是304，客户端有缓冲的文档并发出了一个条件性的请求（一般是提供If-Modified-Since头表示客户
        // 只想比指定日期更新的文档）。服务器告诉客户，原来缓冲的文档还可以继续使用。
        //则使用缓存的响应
        Response response = cacheResponse.newBuilder()
            .headers(combine(cacheResponse.headers(), networkResponse.headers()))
            .sentRequestAtMillis(networkResponse.sentRequestAtMillis())
            .receivedResponseAtMillis(networkResponse.receivedResponseAtMillis())
            .cacheResponse(stripBody(cacheResponse))
            .networkResponse(stripBody(networkResponse))
            .build();
        networkResponse.body().close();

        // Update the cache after combining headers but before stripping the
        // Content-Encoding header (as performed by initContentStream()).
        cache.trackConditionalCacheHit();
        cache.update(cacheResponse, response);
        return response;
      } else {
        closeQuietly(cacheResponse.body());
      }
    }
    //使用网络响应
    Response response = networkResponse.newBuilder()
        .cacheResponse(stripBody(cacheResponse))
        .networkResponse(stripBody(networkResponse))
        .build();
    //所以默认创建的OkHttpClient是没有缓存的
    if (cache != null) {
      //将响应缓存
      if (HttpHeaders.hasBody(response) && CacheStrategy.isCacheable(response, networkRequest)) {
        // Offer this request to the cache.
        //缓存Resposne的Header信息
        CacheRequest cacheRequest = cache.put(response);
        //缓存body
        return cacheWritingResponse(cacheRequest, response);
      }
      //只能缓存GET....不然移除request
      if (HttpMethod.invalidatesCache(networkRequest.method())) {
        try {
          cache.remove(networkRequest);
        } catch (IOException ignored) {
          // The cache cannot be written.
        }
      }
    }

    return response;
  }
```
这里就可以分析CacheInterceptor的主要流程了。
>1.通过Request尝试到Cache中拿缓存（里面非常多流程），当然前提是OkHttpClient中配置了缓存，默认是不支持的。
>2.根据response,time,request创建一个缓存策略，用于判断怎样使用缓存。
>3.如果缓存策略中设置禁止使用网络，并且缓存又为空，则构建一个Resposne直接返回，注意返回码=504
>4.缓存策略中设置不使用网络，但是又缓存，直接返回缓存
>5.接着走后续过滤器的流程，chain.proceed(networkRequest)
>6.当缓存存在的时候，如果网络返回的Resposne为304，则使用缓存的Resposne。
>7.构建网络请求的Resposne
>8.当在OKHttpClient中配置了缓存，则将这个Resposne缓存起来。
>9.缓存起来的步骤也是先缓存header，再缓存body。
>10.返回Resposne。

这里要注意的是2，9两个点。其中2对应的是**CacheStrategy**这个类，**里面主要涉及Http协议中缓存的相关设置，具体的我也没太搞明白，准备入手一本Http的书好好研究研究。**但是这里不影响理解主要流程。
下面就是对9，也就是**存缓存**这个步骤的分析了，其实前面的**取缓存**的分析结束后，这里对存缓存不难猜测其实是想对应的，也就比较好理解了，对应的大体应该是header存入clean[0],body存入clean[1]。这里详细看一下。
```
if (cache != null) {
      //将响应缓存
      if (HttpHeaders.hasBody(response) && CacheStrategy.isCacheable(response, networkRequest)) {
        // Offer this request to the cache.
        //缓存Resposne的Header信息
        CacheRequest cacheRequest = cache.put(response);
        //缓存body
        return cacheWritingResponse(cacheRequest, response);
      }
      //只能缓存GET....不然移除request
      if (HttpMethod.invalidatesCache(networkRequest.method())) {
        try {
          cache.remove(networkRequest);
        } catch (IOException ignored) {
          // The cache cannot be written.
        }
      }
    }
```
当可以缓存的时候，这里用了**cache.put(response)**方法。
```
@Nullable CacheRequest put(Response response) {
    String requestMethod = response.request().method();

    if (HttpMethod.invalidatesCache(response.request().method())) {
      //OKhttp只能缓存GET请求！。。。
      try {
        remove(response.request());
      } catch (IOException ignored) {
        // The cache cannot be written.
      }
      return null;
    }
    if (!requestMethod.equals("GET")) {
      //OKhttp只能缓存GET请求！。。。
      // Don't cache non-GET responses. We're technically allowed to cache
      // HEAD requests and some POST requests, but the complexity of doing
      // so is high and the benefit is low.
      return null;
    }

    if (HttpHeaders.hasVaryAll(response)) {
      return null;
    }

    Entry entry = new Entry(response);
    DiskLruCache.Editor editor = null;
    try {
      editor = cache.edit(key(response.request().url()));
      if (editor == null) {
        return null;
      }
      //缓存了Header信息
      entry.writeTo(editor);
      return new CacheRequestImpl(editor);
    } catch (IOException e) {
      abortQuietly(editor);
      return null;
    }
  }
```
可以看到这里先有几种可能返回null，也就是对应的不能缓存，这里会惊讶的发现！**OkHttpClient源码中支持GET形式的缓存**。
```
 if (!requestMethod.equals("GET")) {
      //OKhttp只能缓存GET请求！。。。
      // Don't cache non-GET responses. We're technically allowed to cache
      // HEAD requests and some POST requests, but the complexity of doing
      // so is high and the benefit is low.
      return null;
    }

public static boolean invalidatesCache(String method) {
    return method.equals("POST")
        || method.equals("PATCH")
        || method.equals("PUT")
        || method.equals("DELETE")
        || method.equals("MOVE");     // WebDAV
  }
```
通过注释其实也可以看到，这里okHttp的开发者认为，从效率角度考虑，最好不要支持POST请求的缓存，暂时只要支持GET形式的缓存。（如果需要支持，对应的其实也就是修改源码，将这里的判断给删除，其实还有一处判断，具体方法Google,Baidu）
```
//缓存了Header信息
      entry.writeTo(editor);
//Entry的writeTo方法===============================
public void writeTo(DiskLruCache.Editor editor) throws IOException {
      //往dirty中写入header信息，ENTRY_METADATA=0，所以是dirtyFiles[0]
      BufferedSink sink = Okio.buffer(editor.newSink(ENTRY_METADATA));

      sink.writeUtf8(url)
          .writeByte('\n');
      sink.writeUtf8(requestMethod)
          .writeByte('\n');
      sink.writeDecimalLong(varyHeaders.size())
          .writeByte('\n');
      for (int i = 0, size = varyHeaders.size(); i < size; i++) {
        sink.writeUtf8(varyHeaders.name(i))
            .writeUtf8(": ")
            .writeUtf8(varyHeaders.value(i))
            .writeByte('\n');
      }

      sink.writeUtf8(new StatusLine(protocol, code, message).toString())
          .writeByte('\n');
      sink.writeDecimalLong(responseHeaders.size() + 2)
          .writeByte('\n');
      for (int i = 0, size = responseHeaders.size(); i < size; i++) {
        sink.writeUtf8(responseHeaders.name(i))
            .writeUtf8(": ")
            .writeUtf8(responseHeaders.value(i))
            .writeByte('\n');
      }
      sink.writeUtf8(SENT_MILLIS)
          .writeUtf8(": ")
          .writeDecimalLong(sentRequestMillis)
          .writeByte('\n');
      sink.writeUtf8(RECEIVED_MILLIS)
          .writeUtf8(": ")
          .writeDecimalLong(receivedResponseMillis)
          .writeByte('\n');

      if (isHttps()) {
        sink.writeByte('\n');
        sink.writeUtf8(handshake.cipherSuite().javaName())
            .writeByte('\n');
        writeCertList(sink, handshake.peerCertificates());
        writeCertList(sink, handshake.localCertificates());
        sink.writeUtf8(handshake.tlsVersion().javaName()).writeByte('\n');
      }
      sink.close();
    }
```
对应写缓存的地方可以看到调用了Entry的writeTo方法，这里别看那么长，其实主要看到一行代码就了解了这个方法的功能了。
```
//往dirty中写入header信息，ENTRY_METADATA=0，所以是dirtyFiles[0]
      BufferedSink sink = Okio.buffer(editor.newSink(ENTRY_METADATA));
```
**还是原来的配方，还是原来的味道，又看到了刚才的参数ENTRY_METADATA=0，可以看到这里对应的其实就是往dirtyFiles[0]中写入header信息，这里其实可以根据前面的分析对应，dirty是用于保存编辑更新等不是持久的数据，而对应的0对应的header,1对应的body。**

```
	//缓存了Header信息
      entry.writeTo(editor);
      return new CacheRequestImpl(editor);
```
写完header后，继续找写body的地方，这里返回了一个CacheRequestImpl对象，一定不要忽略，不然就找不到写body的地方了。
```
CacheRequestImpl(final DiskLruCache.Editor editor) {
      this.editor = editor;
		//ENTRY_BODY = 1
      this.cacheOut = editor.newSink(ENTRY_BODY);
      this.body = new ForwardingSink(cacheOut) {
        @Override public void close() throws IOException {
          synchronized (Cache.this) {
            if (done) {
              return;
            }
            done = true;
            writeSuccessCount++;
          }
          super.close();
          editor.commit();
        }
      };
    }
```
看到ENTRY_BODY就放心， 这里对应的ENTRY_BODY=1对应的就是数组的第二个位置。那到了数据源，接着就要找写入的地方，这里还要注意一个地方**editor.commit();**
```
//CacheIntercetor中==========================
		//缓存Resposne的Header信息
        CacheRequest cacheRequest = cache.put(response);
        //缓存body
        return cacheWritingResponse(cacheRequest, response);
```
可以看到返回了一个CacheRequestImpl对象后，最终执行了一个cacheWritingResponse方法。
```
private Response cacheWritingResponse(final CacheRequest cacheRequest, Response response)
      throws IOException {
    // Some apps return a null body; for compatibility we treat that like a null cache request.
    if (cacheRequest == null) return response;
    Sink cacheBodyUnbuffered = cacheRequest.body();
    if (cacheBodyUnbuffered == null) return response;
    //获得body
    final BufferedSource source = response.body().source();
    final BufferedSink cacheBody = Okio.buffer(cacheBodyUnbuffered);

    Source cacheWritingSource = new Source() {
      boolean cacheRequestClosed;

      @Override public long read(Buffer sink, long byteCount) throws IOException {
        long bytesRead;
        try {
          bytesRead = source.read(sink, byteCount);
        } catch (IOException e) {
          if (!cacheRequestClosed) {
            cacheRequestClosed = true;
            cacheRequest.abort(); // Failed to write a complete cache response.
          }
          throw e;
        }

        if (bytesRead == -1) {
          if (!cacheRequestClosed) {
            cacheRequestClosed = true;
            cacheBody.close(); // The cache response is complete!
          }
          return -1;
        }
        //读的时候会将body写入
        sink.copyTo(cacheBody.buffer(), sink.size() - bytesRead, bytesRead);
        cacheBody.emitCompleteSegments();
        return bytesRead;
      }

      @Override public Timeout timeout() {
        return source.timeout();
      }

      @Override public void close() throws IOException {
        if (!cacheRequestClosed
            && !discard(this, HttpCodec.DISCARD_STREAM_TIMEOUT_MILLIS, MILLISECONDS)) {
          cacheRequestClosed = true;
          //关闭的时候会执行commit操作，最终合并header和body，完成缓存
          cacheRequest.abort();
        }
        source.close();
      }
    };

    String contentType = response.header("Content-Type");
    long contentLength = response.body().contentLength();
    return response.newBuilder()
        .body(new RealResponseBody(contentType, contentLength, Okio.buffer(cacheWritingSource)))
        .build();
  }
```
这里分析一下主要主要流程。
1.获得Resposne中的body
```
//获得body
    final BufferedSource source = response.body().source();
```
2.将Resposne中获得的body写入缓存中，也就是刚在拿到的dirtyfile[1]
```
//读的时候会将body写入
        sink.copyTo(cacheBody.buffer(), sink.size() - bytesRead, bytesRead);
```
可以看到这里bytesRead就是读的Body，最后利用sink.copyTo，写入cacheBody.buffer()中，也就是刚在拿到的dirtyfile[1]。
3.在close中会执行abort操作，对应的里面会执行commit的操作，会将dirtyfile写入cleanfile中，完成持久化保存。
```
@Override public void close() throws IOException {
        if (!cacheRequestClosed
            && !discard(this, HttpCodec.DISCARD_STREAM_TIMEOUT_MILLIS, MILLISECONDS)) {
          cacheRequestClosed = true;
          //关闭的时候会执行commit操作，最终合并header和body，完成缓存
          cacheRequest.abort();
        }
        source.close();
      }
```
可以看到这里再关闭时会执行abort方法。
```
@Override public void abort() {
      synchronized (Cache.this) {
        if (done) {
          return;
        }
        done = true;
        writeAbortCount++;
      }
      Util.closeQuietly(cacheOut);
      try {
        editor.abort();
      } catch (IOException ignored) {
      }
    }
```
对应执行了editor的abort()方法。
```
public void abort() throws IOException {
      synchronized (DiskLruCache.this) {
        if (done) {
          throw new IllegalStateException();
        }
        if (entry.currentEditor == this) {
          completeEdit(this, false);
        }
        done = true;
      }
    }
```
可以看到这里执行了completeEdite方法。
```
synchronized void completeEdit(Editor editor, boolean success) throws IOException {
    ...

    for (int i = 0; i < valueCount; i++) {
      File dirty = entry.dirtyFiles[i];
      if (success) {
        if (fileSystem.exists(dirty)) {
          File clean = entry.cleanFiles[i];
          fileSystem.rename(dirty, clean);
          long oldLength = entry.lengths[i];
          long newLength = fileSystem.size(clean);
          entry.lengths[i] = newLength;
          size = size - oldLength + newLength;
        }
      } else {
        fileSystem.delete(dirty);
      }
    }

    ...
  }
```
这里删点代码吧，贴的代码太多了，这里只放了最重要的一条，可以看到将dirtyFiles数组保存赋值到cleanFiles数组中，完成了最终的持久化保存。

数一下这里的重点吧
>1.缓存中是有日志文件用于保存操作记录
>2.缓存中的Entry有用CleanFiles和DirtyFiles，其中Clean是用于保存持久性数据的，也就是真正保存数据的地方，Dirty是用于保存编辑过程中的数据的。
>3.CleanFiles[]大小为2，第一个保存Header，第二个保存Body，最终保存缓存。


到此。。。结束了。。。没有结束语。
