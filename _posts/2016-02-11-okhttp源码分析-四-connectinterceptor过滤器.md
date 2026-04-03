---
title: okhttp源码分析（四）-ConnectInterceptor过滤器
date: 2017-11-06 23:07:52+08:00
categories: ["Android源码分析"]
source_name: "okhttp源码分析（四）-ConnectInterceptor过滤器"
jianshu_views: 3918
jianshu_url: "https://www.jianshu.com/p/4bf4c796db6f"
---
>1.[okhttp源码分析（一）——基本流程（超详细）](http://www.jianshu.com/p/37e26f4ea57b)
>2.[okhttp源码分析（二）——RetryAndFollowUpInterceptor过滤器](http://www.jianshu.com/p/3b23521f78b6)
>3.[okhttp源码分析（三）——CacheInterceptor过滤器](http://www.jianshu.com/p/bfb13eb3a425)
>4.[okhttp源码分析（四）——ConnectInterceptor过滤器](http://www.jianshu.com/p/4bf4c796db6f)
>5.[okhttp源码分析（五）——CallServerInterceptor过滤器](http://www.jianshu.com/p/4c54e8264971)
### 前言
>前一篇博客分析了CacheInterceptor过滤器，这篇博客主要分析下一个过滤器ConnectInterceptor。其实分析了OkHttp看了这么多代码，学习的不仅仅是OkHttp的处理逻辑和思路，从OkHttp的编程规范和命名规则其实也可以学习很多，就像过滤器，慢慢会发现每个过滤器的名字准确的定位了每个过滤器的任务。 

ConnectInterceptor正如名字所示，是OkHttp中负责和服务器建立连接的过滤器，其实到这里已经可以慢慢意识到OkHttp已经和Android已有的网络框架Volley，Android-async-http等的不同，Volley的底层是提供HttpStack的接口，利用**策略模式**，这里对版本进行了判断，大于等于2.3则创建HttpURLConnection,小于则创建HttpClientStack，也就是说实际上与服务器建立连接的是利用Google提供的两种连接服务器的类（具体可以看我原来分析过的[Volley源码系列](http://www.jianshu.com/p/b409f2bde354)）。也就是说Volley开发的层次面到此也就结束了。但是这里OkHttp的不同点就很明显，OkHttp没有单纯的直接使用上面提到的Google提供的现有的HttpURLConnection等类来直接建立连接，而是专门使用一个过滤器用于建立连接，也就是说在建立连接的层面也有开发和优化（Okio）。我的理解，从开发归属层面来说其实Okhttp是更深层次的，将建立网络请求优化一直衍生到Socket连接的。
### 分析
#### 1.宏观流程
一样的配方，先从大体流程上对这个过滤器进行理解，当然就是看这个过滤器的**intercept**方法。出乎意料的是这个过滤器单从这个方法来看没有成吨的方法和代码行，不需要我们做过多的删减。
```
@Override public Response intercept(Chain chain) throws IOException {
    RealInterceptorChain realChain = (RealInterceptorChain) chain;
    Request request = realChain.request();
    StreamAllocation streamAllocation = realChain.streamAllocation();

    boolean doExtensiveHealthChecks = !request.method().equals("GET");
    //建立HttpCodec
    HttpCodec httpCodec = streamAllocation.newStream(client, chain, doExtensiveHealthChecks);
	//获取连接
    RealConnection connection = streamAllocation.connection();

    return realChain.proceed(request, streamAllocation, httpCodec, connection);
  }
```
可以看到这里流程上看很简单：
>1.建立HttpCodec对象。
>2.调用streamAllocation.connection()获取连接。

所以大体的流程上来看可以看出这个过滤器的作用就是来建立连接的。
#### 2.过程细节
#### （1）HttpCodec
这里第一步是HttpCodec的建立过程。所以理所当然首先要了解一下HttpCodec是个什么东西。
```
/** Encodes HTTP requests and decodes HTTP responses. */
public interface HttpCodec {
  int DISCARD_STREAM_TIMEOUT_MILLIS = 100;
  Sink createRequestBody(Request request, long contentLength);
  void writeRequestHeaders(Request request) throws IOException;
  void flushRequest() throws IOException;
  void finishRequest() throws IOException;
  Response.Builder readResponseHeaders(boolean expectContinue) throws IOException;
  ResponseBody openResponseBody(Response response) throws IOException;
  void cancel();
}
```
不出意外这是个借口，不得不说Okhttp**面向接口**编程的思想体现的真的很好。这里我特意把这个类的注释留了下来，通过注释我们知道了这个接口的作用是**编码和解码HTTP响应HTTP请求**。顺便看一个方法其实也可以看出个大概。
#### （2）streamAllocation.newStream
```
public HttpCodec newStream(
      OkHttpClient client, Interceptor.Chain chain, boolean doExtensiveHealthChecks) {
    int connectTimeout = chain.connectTimeoutMillis();
    int readTimeout = chain.readTimeoutMillis();
    int writeTimeout = chain.writeTimeoutMillis();
    boolean connectionRetryEnabled = client.retryOnConnectionFailure();

    try {
      RealConnection resultConnection = findHealthyConnection(connectTimeout, readTimeout,
          writeTimeout, connectionRetryEnabled, doExtensiveHealthChecks);
      //建立HttpCodec
      HttpCodec resultCodec = resultConnection.newCodec(client, chain, this);

      synchronized (connectionPool) {
        codec = resultCodec;
        return resultCodec;
      }
    } catch (IOException e) {
      throw new RouteException(e);
    }
  }
```
接下来就要看这个HttpCodec的建立过程，可以看到这里其实就两步。
>1.findHealthyConnection找到一条“健康”的连接
>2.建立HttpCodec

这里先看你findHealthyConnection这个方法，一开始我是很懵的，何为“健康”。
```
private RealConnection findHealthyConnection(int connectTimeout, int readTimeout,
      int writeTimeout, boolean connectionRetryEnabled, boolean doExtensiveHealthChecks)
      throws IOException {
    while (true) { //循环查找一个链接
      RealConnection candidate = findConnection(connectTimeout, readTimeout, writeTimeout,
          connectionRetryEnabled);

      // If this is a brand new connection, we can skip the extensive health checks.
      synchronized (connectionPool) {
        if (candidate.successCount == 0) {
          return candidate;
        }
      }
      // Do a (potentially slow) check to confirm that the pooled connection is still good. If it
      // isn't, take it out of the pool and start again.
      //如果这条连接不健康
      if (!candidate.isHealthy(doExtensiveHealthChecks)) {
        //禁止这条连接
        noNewStreams();
        continue;
      }
      return candidate;
    }
  }
```
这里的流程是这样的，其实从方法层面上来看流程还是比较好理解的。
```
RealConnection candidate = findConnection(connectTimeout, readTimeout, writeTimeout,connectionRetryEnabled);
```
1).while循环遍历寻找一个连接，既然是遍历就会发现OkHttp中是存在连接池的概念的，这也是OkHttp中的一个特有的优化。
```
synchronized (connectionPool) {
        if (candidate.successCount == 0) {
          return candidate;
        }
      }
```
2)日常线程安全措施，如果建立的连接candidate是新建立的（新的当然还没有用过，所以successCount=0），直接返回，不再需要后面的“健康检查”。这里的线程安全当然是保证当两个线程同事进行检查的时候发生的情况，保证线程安全。
```
//如果这条连接不健康
      if (!candidate.isHealthy(doExtensiveHealthChecks)) {
        //禁止这条连接
        noNewStreams();
        continue;
      }
```
3)进行安全检查，如果不健康了，禁止这条连接，继续执行循环，继续在连接池中查找能用的连接。
4)返回得到的连接。

这里在来详细看一下1)个步骤，也就是查找健康的连接这个过程findConnection。
```
private RealConnection findConnection(int connectTimeout, int readTimeout, int writeTimeout,
      boolean connectionRetryEnabled) throws IOException {
    boolean foundPooledConnection = false;
    RealConnection result = null;
    Route selectedRoute = null;
    Connection releasedConnection;
    Socket toClose;
    synchronized (connectionPool) {
      if (released) throw new IllegalStateException("released");
      if (codec != null) throw new IllegalStateException("codec != null");
      if (canceled) throw new IOException("Canceled");

      // Attempt to use an already-allocated connection. We need to be careful here because our
      // already-allocated connection may have been restricted from creating new streams.
      releasedConnection = this.connection;
      toClose = releaseIfNoNewStreams();
      if (this.connection != null) {
        //如果当前connection不为空可以直接使用
        // We had an already-allocated connection and it's good.
        result = this.connection;
        releasedConnection = null;
      }
      if (!reportedAcquired) {
        // If the connection was never reported acquired, don't report it as released!
        releasedConnection = null;
      }

      //当前这个connection不能使用，尝试从连接池里面获取一个请求
      if (result == null) {
        // Attempt to get a connection from the pool.
        //Internal是一个抽象类，instance是在OkHttpClient中实现的，get方法实现的时候从pool的get方法
        Internal.instance.get(connectionPool, address, this, null);
        if (connection != null) {
          foundPooledConnection = true;
          result = connection;
        } else {
          selectedRoute = route;
        }
      }
    }
    closeQuietly(toClose);
    //释放一条连接,回调
    if (releasedConnection != null) {
      eventListener.connectionReleased(call, releasedConnection);
    }
    //如果找到复用的，则使用这条连接，回调
    if (foundPooledConnection) {
      eventListener.connectionAcquired(call, result);
    }
    if (result != null) {
      //找到一条可复用的连接
      // If we found an already-allocated or pooled connection, we're done.
      return result;
    }

    // If we need a route selection, make one. This is a blocking operation.
    boolean newRouteSelection = false;
    //切换路由再在连接池里面找下，如果有则返回
    if (selectedRoute == null && (routeSelection == null || !routeSelection.hasNext())) {
      newRouteSelection = true;
      routeSelection = routeSelector.next();
    }

    synchronized (connectionPool) {
      if (canceled) throw new IOException("Canceled");

      if (newRouteSelection) {
        // Now that we have a set of IP addresses, make another attempt at getting a connection from
        // the pool. This could match due to connection coalescing.
        //遍历RooteSelector
        List<Route> routes = routeSelection.getAll();
        for (int i = 0, size = routes.size(); i < size; i++) {
          Route route = routes.get(i);
          Internal.instance.get(connectionPool, address, this, route);
          if (connection != null) {
            foundPooledConnection = true;
            result = connection;
            this.route = route;
            break;
          }
        }
      }

      if (!foundPooledConnection) {
        //没找到则创建一条
        if (selectedRoute == null) {
          selectedRoute = routeSelection.next();
        }

        // Create a connection and assign it to this allocation immediately. This makes it possible
        // for an asynchronous cancel() to interrupt the handshake we're about to do.
        route = selectedRoute;
        refusedStreamCount = 0;
        result = new RealConnection(connectionPool, selectedRoute);
        //往连接中增加流
        acquire(result, false);
      }
    }

    // If we found a pooled connection on the 2nd time around, we're done.
    //如果第二次找到了可以复用的，则返回
    if (foundPooledConnection) {
      eventListener.connectionAcquired(call, result);
      return result;
    }

    // Do TCP + TLS handshakes. This is a blocking operation.
    // 建立连接,开始握手
    result.connect(
        connectTimeout, readTimeout, writeTimeout, connectionRetryEnabled, call, eventListener);
    //将这条路由从错误缓存中清除
    routeDatabase().connected(result.route());

    Socket socket = null;
    synchronized (connectionPool) {
      reportedAcquired = true;

      // Pool the connection.
      //将这个请求加入连接池
      Internal.instance.put(connectionPool, result);

      // If another multiplexed connection to the same address was created concurrently, then
      // release this connection and acquire that one.
      // 如果是多路复用，则合并
      if (result.isMultiplexed()) {
        socket = Internal.instance.deduplicate(connectionPool, address, this);
        result = connection;
      }
    }
    closeQuietly(socket);

    eventListener.connectionAcquired(call, result);
    return result;
  }
```
这里我们一步一步看。首先这里需要提前这个函数体中的相关变量，便于后面对过程的理解。
```
	boolean foundPooledConnection = false;
    RealConnection result = null;
    Route selectedRoute = null;
    Connection releasedConnection;
    Socket toClose;
```
foundPooledConnection对应是否在连接池中找到Connection。
result对应找到的可用的连接。
seletedRoute对应找到的路由。
releasedConnection对应可以释放的连接、
toClose对应需要关闭的连接。
下面开始看流程：
1)
```
	  releasedConnection = this.connection;
      toClose = releaseIfNoNewStreams();
      if (this.connection != null) {
        //如果当前connection不为空可以直接使用
        // We had an already-allocated connection and it's good.
        result = this.connection;
        releasedConnection = null;
      }
```
这里如果当前的StreamAllocation持有的Connection先赋值给releasedConnection，执行releaseIfNoNewStreams()方法获得需要关闭的Socket。如果当前的Connection不为空，则非常棒（注释...）,暂且将这个连接赋值个result，将releasedConnection赋值为空。这里看一下releaseIfNoNewStreams()方法。
```
/**
   * Releases the currently held connection and returns a socket to close if the held connection
   * restricts new streams from being created. With HTTP/2 multiple requests share the same
   * connection so it's possible that our connection is restricted from creating new streams during
   * a follow-up request.
   */
  private Socket releaseIfNoNewStreams() {
    assert (Thread.holdsLock(connectionPool));
    RealConnection allocatedConnection = this.connection;
    if (allocatedConnection != null && allocatedConnection.noNewStreams) {
      return deallocate(false, false, true);
    }
    return null;
  }
```
这里先从看注释看一下，其实注释写的很清楚
>释放当前的连接，返回一个socket为了防止当前的连接限制了新的连接被create。由于Http2多个请求可以用一条连接的特性，所以我们连接可能会限制后续的请求。
从代码上看，先将当前的Connection赋值给需要回收的连接allocatedConnection，如果allocatedConnection不为空（也就是当前的连接不为空），并且当前的连接没有新的流可以创建，则释放这条连接。否则返回空。所以这个方法的作用其实可以归结到以下几点：
>1.如果当前这条连接为空，也就是没有连接，直接返回null.
>2.如果当期这条连接不为空，并且还可以创建流（也就是还可以用），返回null.
>3.如果当前这条连接不为空，并且不能再创建流了（不能用了），回收。

这里看一下回收的方法deallocate。
```
/**
   * Releases resources held by this allocation. If sufficient resources are allocated, the
   * connection will be detached or closed. Callers must be synchronized on the connection pool.
   *
   * <p>Returns a closeable that the caller should pass to {@link Util#closeQuietly} upon completion
   * of the synchronized block. (We don't do I/O while synchronized on the connection pool.)
   */
  private Socket deallocate(boolean noNewStreams, boolean released, boolean streamFinished) {
    assert (Thread.holdsLock(connectionPool));

    if (streamFinished) {
      this.codec = null;
    }
    if (released) {
      this.released = true;
    }
    Socket socket = null;
    if (connection != null) {
      if (noNewStreams) {
        connection.noNewStreams = true;
      }
      if (this.codec == null && (this.released || connection.noNewStreams)) {
        release(connection);
        if (connection.allocations.isEmpty()) {
          connection.idleAtNanos = System.nanoTime();
          if (Internal.instance.connectionBecameIdle(connectionPool, connection)) {
            socket = connection.socket();
          }
        }
        connection = null;
      }
    }
    return socket;
  }
```
从注释上看，其实就可以发现这个方法的作用其实就是回收资源，也就是将所持有的资源至空，关闭。
这里可以看一下做了哪些。
>1.codec = null
>2.released = true
>3.noNewStreams = true
>4.connection = null
>5.返回connection对应的socket

其实可以看到，当这一系列方法执行完后，如果有可以回收关闭的Connection，则最后释放Connection持有的资源后，返回了这个Connection对应的Socket给toClose。接下来看下一步。
2)
```
	  //当前这个connection不能使用，尝试从连接池里面获取一个请求
      if (result == null) {
        // Attempt to get a connection from the pool.
        //Internal是一个抽象类，instance是在OkHttpClient中实现的，get方法实现的时候从pool的get方法
        Internal.instance.get(connectionPool, address, this, null);
        if (connection != null) {
          foundPooledConnection = true;
          result = connection;
        } else {
          selectedRoute = route;
        }
      }
```
可以看到这里如果上面的第一个没有合适的连接，result==null，这时候就是OkHttp的独特之处：**连接池**。
```
Internal.instance.get(connectionPool, address, this, null);


//Internal.java
public abstract class Internal {
  ...
  public static Internal instance;
  ...
}
```
这里可以看到用到了Internal这个对象，这个对象通过查看源码可以发现是一个抽象类，并且实际上调用的是instance对象，看到这个名词其实第一个反应就是**单例模式**，源码上看也没错,这里确实是单例模式中的类似**饿汉模式**。但是不同的是这里的初始化并没有在这里写，其实也难怪，这个类是抽象类，是不能初始化的，所以这里我们就需要找到这个抽象类的实现类。通过寻找可以发现这个类的实现类的初始化是在OkHttpClient中，这里进到源码中看一看。
```
static {
    Internal.instance = new Internal() {
    ...
      @Override public RealConnection get(ConnectionPool pool, Address address,
          StreamAllocation streamAllocation, Route route) {
        return pool.get(address, streamAllocation, route);
      }
    ...
    }
```
这里可以看到这里初始化是在静态代码块中写的，也就是在类加载的时候初始化的，这里我们调用了get方法，其实可以看到实际上调用的是**ConnectionPool.get()**方法。所以继续看源码。
```
/**
   * Returns a recycled connection to {@code address}, or null if no such connection exists. The
   * route is null if the address has not yet been routed.
   */
  @Nullable RealConnection get(Address address, StreamAllocation streamAllocation, Route route) {
    //这种方法的目的是允许一个程序断言当前线程已经持有指定的锁
    assert (Thread.holdsLock(this));
    for (RealConnection connection : connections) {
      if (connection.isEligible(address, route)) {
        //连接池里面存在可以复用的连接
        //往连接池中这条可以复用的连接增加一条流
        streamAllocation.acquire(connection, true);
        return connection;
      }
    }
    return null;
  }
```
注释其实也可以帮助我们理解，这里就不翻译了，其实代码也比较清楚，遍历pool中的connections（ArrayQueue）,如果连接是可以复用的，则将这个连接返回。
这里看一下判断连接可以复用的isEligible()方法。
```
/**
   * Returns true if this connection can carry a stream allocation to {@code address}. If non-null
   * {@code route} is the resolved route for a connection.
   */
  public boolean isEligible(Address address, @Nullable Route route) {
    // If this connection is not accepting new streams, we're done.
    //如果当前这次连接的最大并发数达到上限，false
    if (allocations.size() >= allocationLimit || noNewStreams) return false;

    // If the non-host fields of the address don't overlap, we're done.
    //如果两个address的其他参数不相同，false
    if (!Internal.instance.equalsNonHost(this.route.address(), address)) return false;

    // If the host exactly matches, we're done: this connection can carry the address.
    //如果两个address的url的host相同，true,复用这条连接
    if (address.url().host().equals(this.route().address().url().host())) {
      return true; // This connection is a perfect match.
    }
    //如果上面的不符合，在下面的情况下可以合并连接
    // At this point we don't have a hostname match. But we still be able to carry the request if
    // our connection coalescing requirements are met. See also:
    // https://hpbn.co/optimizing-application-delivery/#eliminate-domain-sharding
    // https://daniel.haxx.se/blog/2016/08/18/http2-connection-coalescing/
    //首先这个连接需要时HTTP/2
    // 1. This connection must be HTTP/2.
    if (http2Connection == null) return false;

    // 2. The routes must share an IP address. This requires us to have a DNS address for both
    // hosts, which only happens after route planning. We can't coalesce connections that use a
    // proxy, since proxies don't tell us the origin server's IP address.
    if (route == null) return false;
    //代理不可以
    if (route.proxy().type() != Proxy.Type.DIRECT) return false;
    if (this.route.proxy().type() != Proxy.Type.DIRECT) return false;
    //IP address需要相同
    if (!this.route.socketAddress().equals(route.socketAddress())) return false;

    // 3. This connection's server certificate's must cover the new host.
    //这个连接的服务器证书必须覆盖新的主机。
    if (route.address().hostnameVerifier() != OkHostnameVerifier.INSTANCE) return false;
    if (!supportsUrl(address.url())) return false;

    // 4. Certificate pinning must match the host.
    //证书将必须匹配主机
    try {
      address.certificatePinner().check(address.url().host(), handshake().peerCertificates());
    } catch (SSLPeerUnverifiedException e) {
      return false;
    }

    return true; // The caller's address can be carried by this connection.
  }
```
这里其实涉及到的其实是比较多的HTTP和HTTP/2的知识，原理细节上准备后期入手本书研究研究，这里其实流程上理解还是比较容易的，总结一下,这里连接池里的一个连接可以复用的判定条件有这几个（注释我写的也比较清楚）：
>1.当前的连接的最大并发数不能达到上限，否则不能复用
>2.两个连接的address的Host不相同，不能复用
>3.1、2通过后，url的host相同则可以复用
>4.如果3中url的host不相同，可以通过合并连接实现复用
>5.但首先这个连接需要时HTTP/2
>6.不能是代理
>7.IP的address要相同
>8.这个连接的服务器证书必须覆盖新的主机
>9.证书将必须匹配主机
>10.以上都不行，则这个连接就不能复用

其实这里主要就是分为两种复用方式：一.host相同直接复用连接。二.如果是HTTP/2，通过其特性合并连接复用。
这里看完判断连接是否合格的方法后，就执行acquire()方法，这里来看一下。
```
/**
//pool中的get方法
   streamAllocation.acquire(connection, true);
//StreamAllocation中的acquire方法
   * Use this allocation to hold {@code connection}. Each call to this must be paired with a call to
   * {@link #release} on the same connection.
   */
  public void acquire(RealConnection connection, boolean reportedAcquired) {
    assert (Thread.holdsLock(connectionPool));
    if (this.connection != null) throw new IllegalStateException();

    this.connection = connection;
    this.reportedAcquired = reportedAcquired;
    //往这条连接中增加一条流
    connection.allocations.add(new StreamAllocationReference(this, callStackTrace));
  }
```
可以看到这里如果通过isEligible()判断通过后，执行acquire方法。
这里讲reportedAcquired设置为true，并向connection持有的allocations中增加了一条新new的流的弱引用，也就是往这条连接中增加了一条流。
至此从连接池中的get方法也分析结束了，要回到我们的主线方法中了，也就是findConnection()方法中。
```
//当前这个connection不能使用，尝试从连接池里面获取一个请求
      if (result == null) {
        // Attempt to get a connection from the pool.
        //Internal是一个抽象类，instance是在OkHttpClient中实现的，get方法实现的时候从pool的get方法
        Internal.instance.get(connectionPool, address, this, null);
        if (connection != null) {
          foundPooledConnection = true;
          result = connection;
        } else {
          selectedRoute = route;
        }
      }
    }
    closeQuietly(toClose);
    //释放一条连接,回调
    if (releasedConnection != null) {
      eventListener.connectionReleased(call, releasedConnection);
    }
    //如果找到复用的，则使用这条连接，回调
    if (foundPooledConnection) {
      eventListener.connectionAcquired(call, result);
    }
    if (result != null) {
      //找到一条可复用的连接
      // If we found an already-allocated or pooled connection, we're done.
      return result;
    }
```
可以看到这里执行完get方法后，如果connection！=null，则标记foundPooledConnection = true,将connection赋值给result，没找到则保存当前路由route到selectedRoute变量。执行完这一系列东西后则是一些关闭和回调操作，最后如果找到了可用的连接，则返回这条可以复用的连接。
3)
```
// If we need a route selection, make one. This is a blocking operation.
    boolean newRouteSelection = false;
    //切换路由再在连接池里面找下，如果有则返回
    if (selectedRoute == null && (routeSelection == null || !routeSelection.hasNext())) {
      newRouteSelection = true;
      routeSelection = routeSelector.next();
    }
```
如果上面没有找到可以复用的连接，则继续执行下面的步骤，可以看这里其实做的是切换路由的操作。
4)
```
synchronized (connectionPool) {
      if (canceled) throw new IOException("Canceled");

      if (newRouteSelection) {
        // Now that we have a set of IP addresses, make another attempt at getting a connection from
        // the pool. This could match due to connection coalescing.
        //遍历RooteSelector
        List<Route> routes = routeSelection.getAll();
        for (int i = 0, size = routes.size(); i < size; i++) {
          Route route = routes.get(i);
          Internal.instance.get(connectionPool, address, this, route);
          if (connection != null) {
            foundPooledConnection = true;
            result = connection;
            this.route = route;
            break;
          }
        }
      }

     ...
    }
```
可以到这里切换完路由后，其实就是遍历路由，再执行一次上面分析过的Internal.instance.get()方法，也就是在切换完路由后再尝试在连接池中寻找可以复用的连接.
5)
```
if (!foundPooledConnection) {
        //没找到则创建一条
        if (selectedRoute == null) {
          selectedRoute = routeSelection.next();
        }

        // Create a connection and assign it to this allocation immediately. This makes it possible
        // for an asynchronous cancel() to interrupt the handshake we're about to do.
        route = selectedRoute;
        refusedStreamCount = 0;
        result = new RealConnection(connectionPool, selectedRoute);
        //往连接中增加流
        acquire(result, false);
      }
```
如果经历了上面的操作后还是没有找到可以复用的连接，那么则创建一个新的连接，终于看到了RealConnection的构造方法，new了一个新的RealConnection,并赋值给result，并执行了上面分析过的acquire()方法，往new的连接中加入了流。
6)
当然这里还没有说如果刚在交换路由后找到可以复用的连接怎么办，接着往下看。
```
// If we found a pooled connection on the 2nd time around, we're done.
    //如果第二次找到了可以复用的，则返回
    if (foundPooledConnection) {
      eventListener.connectionAcquired(call, result);
      return result;
    }
```
可以看到如果第二次找到了，同样回调，然后返回找到的连接。
7)
```
// Do TCP + TLS handshakes. This is a blocking operation.
    // 建立连接,开始握手
    result.connect(
        connectTimeout, readTimeout, writeTimeout, connectionRetryEnabled, call, eventListener);
    //将这条路由从错误缓存中清除
    

    Socket socket = null;
    synchronized (connectionPool) {
      reportedAcquired = true;

      // Pool the connection.
      //将这个请求加入连接池
      Internal.instance.put(connectionPool, result);

      // If another multiplexed connection to the same address was created concurrently, then
      // release this connection and acquire that one.
      // 如果是多路复用，则合并
      if (result.isMultiplexed()) {
        socket = Internal.instance.deduplicate(connectionPool, address, this);
        result = connection;
      }
    }
    closeQuietly(socket);

    eventListener.connectionAcquired(call, result);
    return result;
```
接下来的这些代码都是**基于没有找到可以复用的连接**这一前提下的，没有找到可以复用的，则是上面6)new出来的新的连接，所以接下来的代码就是执行connect()方法，里面其实就涉及到三次握手连接流程了。
后面执行的这行代码特意说一下，```routeDatabase().connected(result.route());```
单从代码上看，可能只是理解为往数据库记录了下这个路由的记录，但是详细进入看一下源码。
```
public final class RouteDatabase {
  //这个太屌了，错误缓存，错误过的连接会被缓存，防止错误请求重复请求
  private final Set<Route> failedRoutes = new LinkedHashSet<>();

  /** Records a failure connecting to {@code failedRoute}. */
  public synchronized void failed(Route failedRoute) {
    failedRoutes.add(failedRoute);
  }

  /** Records success connecting to {@code route}. */
  public synchronized void connected(Route route) {
    failedRoutes.remove(route);
  }

  /** Returns true if {@code route} has failed recently and should be avoided. */
  public synchronized boolean shouldPostpone(Route route) {
    return failedRoutes.contains(route);
  }
}
```
代码很简单，思想和全面，用Set<>集合保存错误过的数据集，因为是new出来的连接，所有肯定没有错误，所以讲这个路由从set中移除，防止多余的检测，那么对应的就可以联想到这里肯定有如果路由发生过错误的记录，每次使用前先检查一下，如果原来错误过，就不用执行后面的流程了（考虑的很全面有木有，相当于缓存了发生过错误的信息）
执行完这个后，就将这new得到的连接加入连接池，
```Internal.instance.put(connectionPool, result);```
后面还有个多路合并的判断，但是具体细节这里就不深入了（需要详细了解HTTP+底层代码）。
**至此**：findConnection（）分析完了，这里大体总结一下流程吧：
>1.尝试当前连接是否可以复用。
>2.尝试连接池中找可以复用的连接
>3.切换路由，继续在连接中尝试找可以复用的连接
>4.以上都没有则new一个新的。

到这里其实findHealthyConnection()也分析完了，过程在上上上……上面已经分析了。。。再回到主流程上了。
```
try {
      RealConnection resultConnection = findHealthyConnection(connectTimeout, readTimeout,
          writeTimeout, connectionRetryEnabled, doExtensiveHealthChecks);
      //建立HttpCodec
      HttpCodec resultCodec = resultConnection.newCodec(client, chain, this);

      synchronized (connectionPool) {
        codec = resultCodec;
        return resultCodec;
      }
    } catch (IOException e) {
      throw new RouteException(e);
    }
```
可以看到找到健康的连接后，执行了newCodec方法，得到了HttpCodec实例，这个上面我们已经分析过了，是一个接口，只是这里再放一下，便于回顾：
```
Encodes HTTP requests and decodes HTTP responses
```
这里就看一下newCodec方法
```
public HttpCodec newCodec(OkHttpClient client, Interceptor.Chain chain,
      StreamAllocation streamAllocation) throws SocketException {
    if (http2Connection != null) {
      return new Http2Codec(client, chain, streamAllocation, http2Connection);
    } else {
      socket.setSoTimeout(chain.readTimeoutMillis());
      source.timeout().timeout(chain.readTimeoutMillis(), MILLISECONDS);
      sink.timeout().timeout(chain.writeTimeoutMillis(), MILLISECONDS);
      return new Http1Codec(client, streamAllocation, source, sink);
    }
  }
```
可以看到这里其实就是判断是Http还是Http2，然后根据**策略模式**最后返回。
至此ConnectInterceptor过滤器的的全部流程就分析完了。再放一下主要方法的代码：
```
@Override public Response intercept(Chain chain) throws IOException {
    RealInterceptorChain realChain = (RealInterceptorChain) chain;
    Request request = realChain.request();
    StreamAllocation streamAllocation = realChain.streamAllocation();

    // We need the network to satisfy this request. Possibly for validating a conditional GET.
    boolean doExtensiveHealthChecks = !request.method().equals("GET");
    //建立HttpCodec
    HttpCodec httpCodec = streamAllocation.newStream(client, chain, doExtensiveHealthChecks);
	//返回RealConnection
    RealConnection connection = streamAllocation.connection();

    return realChain.proceed(request, streamAllocation, httpCodec, connection);
  }
```

到此。。。结束了。。。没有结束语。
