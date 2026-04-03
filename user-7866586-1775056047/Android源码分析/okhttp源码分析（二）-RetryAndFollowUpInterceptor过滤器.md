>1.[okhttp源码分析（一）——基本流程（超详细）](http://www.jianshu.com/p/37e26f4ea57b)
>2.[okhttp源码分析（二）——RetryAndFollowUpInterceptor过滤器](http://www.jianshu.com/p/3b23521f78b6)
>3.[okhttp源码分析（三）——CacheInterceptor过滤器](http://www.jianshu.com/p/bfb13eb3a425)
>4.[okhttp源码分析（四）——ConnectInterceptor过滤器](http://www.jianshu.com/p/4bf4c796db6f)
>5.[okhttp源码分析（五）——CallServerInterceptor过滤器](http://www.jianshu.com/p/4c54e8264971)
### 前言
紧接着上一篇基本流程分析完后，准备的是将过滤器分析分析，过滤器可以说是OkHttp的点睛之笔。这一篇主要分析RetryAndFollowUpInterceptor这个过滤器，首先从名字我们就可以明白这个过滤器的职责是重试和重定向。
### 分析
#### 1.宏观流程
读过上一篇博客的人应该都清楚看一个过滤器的功能，重点都在他重写Interceptor的```intercept(Chain chain)```方法。
打开源码突然发现这么长。。。不要绝望，我按照我的理解将代码处理一下，我们先从流程看起，至少从宏观上要对这个过滤器有个认识。
```
@Override public Response intercept(Chain chain) throws IOException {
	。。。
    while (true) {
    。。。
      try {
        response = realChain.proceed(request, streamAllocation, null, null);
      }
	。。。
	if(满足条件){
		return response;
	}
	。。。
      //不满足条件，一顿操作，赋值再来！
      request = followUp;
      priorResponse = response;
    }
  }
```
其实就流程来上，我认为宏观上代码缩减到这样就够了，甚至可以再删点，这里先从流程上理解.
其实代码成这样，基本上大家都能理解了，一个while(true)表明这是个循环体，循环体主要做的事可以看到其实是递归的主要方法。
```
response = realChain.proceed(request, streamAllocation, null, null);
```
执行了这个方法后，就会交给下一个过滤器继续执行，所以单从这里来看，我们可以简单的理解为这个过滤器其实没做什么。
但是当出现了一些问题，导致不满足条件的时候，就需要进行一系列的操作，重新复制Request，重新请求，这也就是while的功能，对应的也就是这个过滤器的主要功能：重试和重定向。
这里我们宏观上已经对RetryAndFollowUpInterceptor有了一个基本的理解了。
#### 2.过程细节
```
@Override public Response intercept(Chain chain) throws IOException {
    Request request = chain.request();
    RealInterceptorChain realChain = (RealInterceptorChain) chain;
    Call call = realChain.call();
    EventListener eventListener = realChain.eventListener();
    //streamAllocation的创建位置
    streamAllocation = new StreamAllocation(client.connectionPool(), createAddress(request.url()),
        call, eventListener, callStackTrace);

    int followUpCount = 0;
    Response priorResponse = null;
    while (true) {
	  //取消
      if (canceled) {
        streamAllocation.release();
        throw new IOException("Canceled");
      }

      Response response;
      boolean releaseConnection = true;
      try {
        response = realChain.proceed(request, streamAllocation, null, null);
        releaseConnection = false;
      } catch (RouteException e) {
        // The attempt to connect via a route failed. The request will not have been sent.
        if (!recover(e.getLastConnectException(), false, request)) {
          throw e.getLastConnectException();
        }
        releaseConnection = false;
        //重试。。。
        continue;
      } catch (IOException e) {
        // An attempt to communicate with a server failed. The request may have been sent.
        //先判断当前请求是否已经发送了
        boolean requestSendStarted = !(e instanceof ConnectionShutdownException);
        //同样的重试判断
        if (!recover(e, requestSendStarted, request)) throw e;
        releaseConnection = false;
        //重试。。。
        continue;
      } finally {
        // We're throwing an unchecked exception. Release any resources.
        //没有捕获到的异常，最终要释放
        if (releaseConnection) {
          streamAllocation.streamFailed(null);
          streamAllocation.release();
        }
      }

      // Attach the prior response if it exists. Such responses never have a body.
      //这里基本上都没有讲，priorResponse是用来保存前一个Resposne的，这里可以看到将前一个Response和当前的Resposne
      //结合在一起了，对应的场景是，当获得Resposne后，发现需要重定向，则将当前Resposne设置给priorResponse，再执行一遍流程，
      //直到不需要重定向了，则将priorResponse和Resposne结合起来。
      if (priorResponse != null) {
        response = response.newBuilder()
            .priorResponse(priorResponse.newBuilder()
                    .body(null)
                    .build())
            .build();
      }
      //判断是否需要重定向,如果需要重定向则返回一个重定向的Request，没有则为null
      Request followUp = followUpRequest(response);

      if (followUp == null) {
        //不需要重定向
        if (!forWebSocket) {
          //是WebSocket,释放
          streamAllocation.release();
        }
        //返回response
        return response;
      }
      //需要重定向，关闭响应流
      closeQuietly(response.body());
      //重定向次数++,并且小于最大重定向次数MAX_FOLLOW_UPS（20）
      if (++followUpCount > MAX_FOLLOW_UPS) {
        streamAllocation.release();
        throw new ProtocolException("Too many follow-up requests: " + followUpCount);
      }
      //是UnrepeatableRequestBody， 刚才看过也就是是流类型，没有被缓存，不能重定向
      if (followUp.body() instanceof UnrepeatableRequestBody) {
        streamAllocation.release();
        throw new HttpRetryException("Cannot retry streamed HTTP body", response.code());
      }
      //判断是否相同，不然重新创建一个streamConnection
      if (!sameConnection(response, followUp.url())) {
        streamAllocation.release();
        streamAllocation = new StreamAllocation(client.connectionPool(),
            createAddress(followUp.url()), call, eventListener, callStackTrace);
      } else if (streamAllocation.codec() != null) {
        throw new IllegalStateException("Closing the body of " + response
            + " didn't close its backing stream. Bad interceptor?");
      }
      //赋值再来！
      request = followUp;
      priorResponse = response;
    }
  }
```
现在就要从源码上具体学习理解这个过滤器了。这里我具体一点一点分析。
```
//streamAllocation的创建位置
    streamAllocation = new StreamAllocation(client.connectionPool(), createAddress(request.url()),
        call, eventListener, callStackTrace);
```
首先第一个点，这里可以看到这里对streamAllocation进行了初始化操作，其实在过滤器的链式调用的过程中会陆陆续续创建一系列对应的参数，这一点从最初的创建Chain的时候就可以看出来，可以看到一开始有很多参数是以null传入的。
```
Response getResponseWithInterceptorChain() throws IOException {
	。。。
    Interceptor.Chain chain = new RealInterceptorChain(interceptors, null, null, null, 0,
        originalRequest, this, eventListener, client.connectTimeoutMillis(),
        client.readTimeoutMillis(), client.writeTimeoutMillis());
	。。。
    return chain.proceed(originalRequest);
  }
```
这里先大概说一下StreamAllocation这个对象是干什么的。这个类大概可以理解为是处理Connections,Streams,Calls三者之间的关系，这一点其实从构造函数的传参也可以看出来。
接下来就要进入循环体中看了，首先可以看到当请求被取消的时候，会跳出循环体（第一种跳出的情况）。
```
	boolean releaseConnection = true;
	try {
        response = realChain.proceed(request, streamAllocation, null, null);
        releaseConnection = false;
      } catch (RouteException e) {
        // The attempt to connect via a route failed. The request will not have been sent.
        if (!recover(e.getLastConnectException(), false, request)) {
          throw e.getLastConnectException();
        }
        releaseConnection = false;
        //重试。。。
        continue;
      }
```
接下来看try catch体中的内容，try其实很简单，就是执行后续过滤器链中的东西，这里要稍微注意一下**releaseConnection**这个变量的，对后续的判断理解是有影响的，可以看到初始化时将releaseConnection这个变量赋值为true。
**下面是重点内容了：**
进入catch体中，可以看到会捕获很多okHttp自定义的Exception，从名字上可以有一个大体上的理解，但是还是要从源码上分析，这里先看第一个异常RouteException，先理解理解注释：**尝试连接一个路由失败，这个请求还没有被发出**，接下来执行了一个方法recover(),这里注意一下**false**参数，现在进入方法体中。
```
private boolean recover(IOException e, boolean requestSendStarted, Request userRequest) {
    streamAllocation.streamFailed(e);

    // The application layer has forbidden retries.
    //如果OkHttpClient直接配置拒绝失败重连，return false
    if (!client.retryOnConnectionFailure()) return false;

    // We can't send the request body again.
    //如果请求已经发送，并且这个请求体是一个UnrepeatableRequestBody类型，则不能重试。
    //StreamedRequestBody实现了UnrepeatableRequestBody接口，是个流类型，不会被缓存，所以只能执行一次，具体可看。
    if (requestSendStarted && userRequest.body() instanceof UnrepeatableRequestBody) return false;

    // This exception is fatal.
    //一些严重的问题，就不要重试了
    if (!isRecoverable(e, requestSendStarted)) return false;

    // No more routes to attempt.
    //没有更多的路由就不要重试了
    if (!streamAllocation.hasMoreRoutes()) return false;

    // For failure recovery, use the same route selector with a new connection.
    return true;
  }
``` 
可以看到这里面有很多的if判断，这里先看第一个。
```
if (!client.retryOnConnectionFailure()) return false;

//==========OkHttpClient.java===========
public boolean retryOnConnectionFailure() {
    return retryOnConnectionFailure;
  }
```
代码一放上来其实就很好理解了，如果我们在配置OkHttpClient中配置retryOnConnectionFailure属性为false，表明拒绝失败重连，那么这里返回false（第一种拒绝重连的方式）。**这里另外说明一下如果我们默认方式创建OkHttpClient的话，retryOnConnectionFailure属性是true**。
```
if (requestSendStarted && userRequest.body() instanceof UnrepeatableRequestBody) return false;
```
下面一个判断首先要明白参数的含义，这里requestSendStarted这个参数就是刚才在recover方法中的第二个参数，是为了表明请求是否已经被发送，这里这里为false，但是这个判断我们需要了解清楚。
单单从判断条件我们可以理解为：**如果请求已经发送，并且这个请求体是一个UnrepeatableRequestBody类型，则不能重试(第二种拒绝重连的方式)。**
这里就要说明一下UnrepeatableRequestBody这个类了。
```
public interface UnrepeatableRequestBody {
}
```
这就是UnrepeatableRequestBody的源码，没有看错...就是一个空的接口，作用就是标记那些不能被重复请求的请求体，这时候可能就想要了解一下那些请求是不能被重复请求的哪？看一下那些Request实现了这个接口，结果会发现，**到目前Okhttp源码中，只有一种请求实现了这个接口，那就是StreamedRequestBody。**
```
/**
 * This request body streams bytes from an application thread to an OkHttp dispatcher thread via a
 * pipe. Because the data is not buffered it can only be transmitted once.
 */
  final class StreamedRequestBody extends OutputStreamRequestBody implements UnrepeatableRequestBody {}
```
从这个类的注释我们也可以理解，StreamedRequestBody实现了UnrepeatableRequestBody接口，是个流类型，不会被缓存，所以只能执行一次。

```
if (!isRecoverable(e, requestSendStarted)) return false;

//=====================isRecoverable()=====================
private boolean isRecoverable(IOException e, boolean requestSendStarted) {
    // If there was a protocol problem, don't recover.
    //如果是协议问题，不要在重试了
    if (e instanceof ProtocolException) {
      return false;
    }

    // If there was an interruption don't recover, but if there was a timeout connecting to a route
    // we should try the next route (if there is one).
    if (e instanceof InterruptedIOException) {
      //超时问题，并且请求还没有被发送，可以重试
      //其他就不要重试了
      return e instanceof SocketTimeoutException && !requestSendStarted;
    }

    // Look for known client-side or negotiation errors that are unlikely to be fixed by trying
    // again with a different route.
    if (e instanceof SSLHandshakeException) {
      // If the problem was a CertificateException from the X509TrustManager,
      // do not retry.
      //理解为如果是安全原因，就不要重试了
      if (e.getCause() instanceof CertificateException) {
        return false;
      }
    }
    if (e instanceof SSLPeerUnverifiedException) {
      // e.g. a certificate pinning error.
      //安全原因
      return false;
    }

    // An example of one we might want to retry with a different route is a problem connecting to a
    // proxy and would manifest as a standard IOException. Unless it is one we know we should not
    // retry, we return true and try a new route.
    return true;
  }
```
下面一个判断可以总体理解为：如果是一些严重的问题（协议，安全...），拒绝重试（第三种拒绝重连的方式）
这里可以看到判断被归结到一个isRecoverable（）的方法中，注释页写的很清楚，这里严重的情况主要由这几种：
* 1.协议问题，不能重试。
* 2.如果是超时问题，并且请求没有被发送，可以重试，其他的就不要重试了。
* 3.安全问题，不要重试。

```
if (!streamAllocation.hasMoreRoutes()) return false;

//========================StreamAllocation.java=====================
public boolean hasMoreRoutes() {
    return route != null
        || (routeSelection != null && routeSelection.hasNext())
        || routeSelector.hasNext();
  }
```
下面这个判断表明：没有更多的可以使用的路由，则不要重试了（第四种拒绝重连的方式）
这里也列出了hasMoreRoutes()方法，可以看到，这里面当游标在最末尾，也就是保存的路由的容器已经遍历完了，也就没办法继续重试了。**这里大概说明一下routeSelection是用List保存的。**
```
catch (RouteException e) {
        // The attempt to connect via a route failed. The request will not have been sent.
        if (!recover(e.getLastConnectException(), false, request)) {
          throw e.getLastConnectException();
        }
        releaseConnection = false;
        //重试。。。
        continue;
      }
```
所以当以上判断结束后，如果需要重试，则continue，重新执行while循环体，也就是发挥了这个过滤器的作用，**重试**

```
catch (IOException e) {
        // An attempt to communicate with a server failed. The request may have been sent.
        //先判断当前请求是否已经发送了
        boolean requestSendStarted = !(e instanceof ConnectionShutdownException);
        //同样的重试判断
        if (!recover(e, requestSendStarted, request)) throw e;
        releaseConnection = false;
        //重试。。。
        continue;
      }
```
这时候看一下下一个异常IOException，首先可以看到，需要先判断请求是否已经发送了，紧接着继续刚才分析的方法recover(),这时默认传的就不是false，而是判断得到的requestSendStarted。最后同样当需要重试时，continue。
```
finally {
        // We're throwing an unchecked exception. Release any resources.
        //没有捕获到的异常，最终要释放
        if (releaseConnection) {
          streamAllocation.streamFailed(null);
          streamAllocation.release();
        }
      }
```
finally体中的内容比较好理解，由于releaseConnection初始化为true，而当正常执行`realChain.proceed`或在执行过程中捕捉到异常时设置为false，所以当执行过程中捕捉到没有检测到的异常时，需要释放一些内容。(此处感谢[@messi_wpy](https://www.jianshu.com/u/8fd672f63550)的指正)

```
if (priorResponse != null) {
        response = response.newBuilder()
            .priorResponse(priorResponse.newBuilder()
                    .body(null)
                    .build())
            .build();
      }
```
接下来这段代码一开始是我比较难以理解的，而且网上其他分析这个过滤器的都没有分析这块，最后自己分析，理解为priorResponse是用来保存前一个Resposne的，这里可以看到将前一个Response和当前的Resposne结合在一起了。对应的场景是：**当获得Resposne后，发现需要重定向，则将当前Resposne设置给priorResponse，再执行一遍流程，直到不需要重定向了，则将priorResponse和Resposne结合起来。**
```
   Request followUp = followUpRequest(response);

//=========================followUpRequest()==============================
private Request followUpRequest(Response userResponse) throws IOException {
    if (userResponse == null) throw new IllegalStateException();
    Connection connection = streamAllocation.connection();
    Route route = connection != null
        ? connection.route()
        : null;
    int responseCode = userResponse.code();

    final String method = userResponse.request().method();
    switch (responseCode) {
      case HTTP_PROXY_AUTH:
        Proxy selectedProxy = route != null
            ? route.proxy()
            : client.proxy();
        if (selectedProxy.type() != Proxy.Type.HTTP) {
          throw new ProtocolException("Received HTTP_PROXY_AUTH (407) code while not using proxy");
        }
        return client.proxyAuthenticator().authenticate(route, userResponse);

      case HTTP_UNAUTHORIZED:
        return client.authenticator().authenticate(route, userResponse);

      case HTTP_PERM_REDIRECT:
      case HTTP_TEMP_REDIRECT:
        // "If the 307 or 308 status code is received in response to a request other than GET
        // or HEAD, the user agent MUST NOT automatically redirect the request"
        if (!method.equals("GET") && !method.equals("HEAD")) {
          return null;
        }
        // fall-through
      case HTTP_MULT_CHOICE:
      case HTTP_MOVED_PERM:
      case HTTP_MOVED_TEMP:
      case HTTP_SEE_OTHER:
        // Does the client allow redirects?
        if (!client.followRedirects()) return null;

        String location = userResponse.header("Location");
        if (location == null) return null;
        HttpUrl url = userResponse.request().url().resolve(location);

        // Don't follow redirects to unsupported protocols.
        if (url == null) return null;

        // If configured, don't follow redirects between SSL and non-SSL.
        boolean sameScheme = url.scheme().equals(userResponse.request().url().scheme());
        if (!sameScheme && !client.followSslRedirects()) return null;

        // Most redirects don't include a request body.
        Request.Builder requestBuilder = userResponse.request().newBuilder();
        if (HttpMethod.permitsRequestBody(method)) {
          final boolean maintainBody = HttpMethod.redirectsWithBody(method);
          if (HttpMethod.redirectsToGet(method)) {
            requestBuilder.method("GET", null);
          } else {
            RequestBody requestBody = maintainBody ? userResponse.request().body() : null;
            requestBuilder.method(method, requestBody);
          }
          if (!maintainBody) {
            requestBuilder.removeHeader("Transfer-Encoding");
            requestBuilder.removeHeader("Content-Length");
            requestBuilder.removeHeader("Content-Type");
          }
        }

        // When redirecting across hosts, drop all authentication headers. This
        // is potentially annoying to the application layer since they have no
        // way to retain them.
        if (!sameConnection(userResponse, url)) {
          requestBuilder.removeHeader("Authorization");
        }
        //重新构造了一个Request
        return requestBuilder.url(url).build();

      case HTTP_CLIENT_TIMEOUT:
        // 408's are rare in practice, but some servers like HAProxy use this response code. The
        // spec says that we may repeat the request without modifications. Modern browsers also
        // repeat the request (even non-idempotent ones.)
        if (!client.retryOnConnectionFailure()) {
          // The application layer has directed us not to retry the request.
          return null;
        }

        if (userResponse.request().body() instanceof UnrepeatableRequestBody) {
          return null;
        }

        if (userResponse.priorResponse() != null
            && userResponse.priorResponse().code() == HTTP_CLIENT_TIMEOUT) {
          // We attempted to retry and got another timeout. Give up.
          return null;
        }

        return userResponse.request();

      default:
        return null;
    }
  }
```
下面这行代码主要是对followUpRequest()这个方法的理解，代码我也粘出来了，这里其实没必要在意每一行代码，这样反而影响我们阅读，这里主要可以观察发现，其实这个方法的主要操作就是，**当返回码满足某些条件时就重新构造一个Request，不满足就返回null**,所以接下来的代码就很容易理解了。
```
if (followUp == null) {
        //不需要重定向
        if (!forWebSocket) {
          //是WebSocket,释放
          streamAllocation.release();
        }
        //返回response
        return response;
      }
```
当不需要重定向，也就是返回的为null,直接返回response。
```
	  //需要重定向，关闭响应流
      closeQuietly(response.body());
      //重定向次数++,并且小于最大重定向次数MAX_FOLLOW_UPS（20）
      if (++followUpCount > MAX_FOLLOW_UPS) {
        streamAllocation.release();
        throw new ProtocolException("Too many follow-up requests: " + followUpCount);
      }
      //是UnrepeatableRequestBody， 刚才看过也就是是流类型，没有被缓存，不能重定向
      if (followUp.body() instanceof UnrepeatableRequestBody) {
        streamAllocation.release();
        throw new HttpRetryException("Cannot retry streamed HTTP body", response.code());
      }
	  //判断是否相同，不然重新创建一个streamConnection
      if (!sameConnection(response, followUp.url())) {
        streamAllocation.release();
        streamAllocation = new StreamAllocation(client.connectionPool(),
            createAddress(followUp.url()), call, eventListener, callStackTrace);
      } else if (streamAllocation.codec() != null) {
        throw new IllegalStateException("Closing the body of " + response
            + " didn't close its backing stream. Bad interceptor?");
      }
      //赋值再来！
      request = followUp;
      priorResponse = response;

//==========================sameConnection()======================
private boolean sameConnection(Response response, HttpUrl followUp) {
    HttpUrl url = response.request().url();
    return url.host().equals(followUp.host())
        && url.port() == followUp.port()
        && url.scheme().equals(followUp.scheme());
  }
```
下面的代码当然就是当返回的不为空，也就是重新构造了一个Request，需要重定向。
* 1.首先关闭响应流。
* 2.增加重定向的次数，保证小于最大重定向次数MAX_FOLLOW_UPS（20）
* 3.不能是UnrepeatableRequestBody类型，刚才也分析过，是一个空接口，用于标记那些只能请求一次的请求。
* 4.判断是否相同，如果不相同，则需要重新创建一个streamConnection。
* 5.重新赋值，结束当前循环，继续while循环，也就是执行重定向请求。


### 总结
到此，RetryAndFollowUpInterceptor这个过滤器已经大体分析完了，总体流程下来可以发现，这个过滤器的主要作用就是用于对请求的重试和重定向的。
其中拒绝重试的判断条件有如下几种：
* 1.如果我们在配置OkHttpClient中配置retryOnConnectionFailure属性为false，表明拒绝失败重连，那么这里返回false
* 2.如果请求已经发送，并且这个请求体是一个UnrepeatableRequestBody类型，则不能重试
* 3.如果是一些严重的问题（协议，安全...），拒绝重试
* 4.没有更多的可以使用的路由，则不要重试了
