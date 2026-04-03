---
title: "okhttp源码分析（五）-CallServerInterceptor过滤器"
date: 2016-02-10 08:00:00 +0800
categories: ["Android源码分析"]
source_name: "okhttp源码分析（五）-CallServerInterceptor过滤器"
---
>1.[okhttp源码分析（一）——基本流程（超详细）](http://www.jianshu.com/p/37e26f4ea57b)
>2.[okhttp源码分析（二）——RetryAndFollowUpInterceptor过滤器](http://www.jianshu.com/p/3b23521f78b6)
>3.[okhttp源码分析（三）——CacheInterceptor过滤器](http://www.jianshu.com/p/bfb13eb3a425)
>4.[okhttp源码分析（四）——ConnectInterceptor过滤器](http://www.jianshu.com/p/4bf4c796db6f)
>5.[okhttp源码分析（五）——CallServerInterceptor过滤器](http://www.jianshu.com/p/4c54e8264971)

### 前言
>终于到最后一个过滤器了，其实阅读源码的过程中有过想要放弃的想法，因为通过查看OkHttp的源码随着逐步深入会逐渐发现OkHttp其实相较于[Volley](http://www.jianshu.com/p/b409f2bde354)来说更像一个对于Http协议封装优化的一个网络框架，从请求的开始一直延伸到到Socket的建立和通信，阅读起来给人感觉更枯燥。

从过滤器的责任链一直到这个过滤器，这个过滤器的功能其实就是负责网络通信最后一个步骤：**数据交换**，也就是负责向服务器发送请求数据、从服务器读取响应数据(实际网络请求)。
### 分析
#### 1.宏观流程
直接上简化过的代码吧
```
@Override public Response intercept(Chain chain) throws IOException {
    //开始写入header
    httpCodec.writeRequestHeaders(request);
    //当Header为Expect: 100-continue时，只发送请求头
    if ("100-continue".equalsIgnoreCase(request.header("Expect"))) {
      httpCodec.flushRequest();
      responseBuilder = httpCodec.readResponseHeaders(true);
    }
    //写入请求体
     request.body().writeTo(bufferedRequestBody);
    //写入完成
	...
    //结束请求
    httpCodec.finishRequest();

    //得到响应头
    responseBuilder = httpCodec.readResponseHeaders(false);
	//构建初步响应
    Response response = responseBuilder
        .request(request)
        .handshake(streamAllocation.connection().handshake())
        .sentRequestAtMillis(sentRequestMillis)
        .receivedResponseAtMillis(System.currentTimeMillis())
        .build();
    ...
      //构建响应体
      response = response.newBuilder()
          .body(httpCodec.openResponseBody(response))
          .build();
    }
	。。。
    //返回响应
    return response;
  }
```
这里流程上其实就比较清楚了，这个过滤器的作用是数据交换，也就会说发送请求和得到响应。
这里大致流程分为：
>1.先写入请求Header
>2.如果请求头的Expect: 100-continue时，只发送请求头，执行3，不然执行4
>3.根据后台返回的结果判断是否继续请求流程
>4.写入请求体，完成请求
>5.得到响应头，构建初步响应
>6.构建响应体，完成最终响应
>7.返回响应
#### 2.过程细节
##### 1.写入Header
```
	//开始写入header
    realChain.eventListener().requestHeadersStart(realChain.call());
    httpCodec.writeRequestHeaders(request);
    //写入结束
    realChain.eventListener().requestHeadersEnd(realChain.call(), request);
```
其实通过事件回调就可以看出来这个步骤的作用是写入Header，这里调用了HttpCodec的writeRequestHeaders的方法，看过前面分析的应该知道HttpCodec其实是一个接口，对应的使用**策略模式**分别根据是Http还是Http/2请求，这里就看一下Http1Codec的实现吧。
```
@Override public void writeRequestHeaders(Request request) throws IOException {
    String requestLine = RequestLine.get(
        request, streamAllocation.connection().route().proxy().type());
    //写入header
    writeRequest(request.headers(), requestLine);
  }


//RequestLine.java
  /**
   * Returns the request status line, like "GET / HTTP/1.1". This is exposed to the application by
   * {@link HttpURLConnection#getHeaderFields}, so it needs to be set even if the transport is
   * HTTP/2.
   */
  //构建"GET / HTTP/1.1"形式的请求状态行
  public static String get(Request request, Proxy.Type proxyType) {
    StringBuilder result = new StringBuilder();
    result.append(request.method());
    result.append(' ');

    if (includeAuthorityInRequestLine(request, proxyType)) {
      result.append(request.url());
    } else {
      result.append(requestPath(request.url()));
    }

    result.append(" HTTP/1.1");
    return result.toString();
  }

```
其实代码还是比较好理解的，这里可以看到首先调用RequestLine的get方法获得一个请求行，这里方法源码也放上来了，其实代码很好理解，可以根据注释或者自己看代码，都会发现最后返回的是类似于```"GET / HTTP/1.1"```的字符串。最后调用writeRequest方法写入Header信息。
```
/** Returns bytes of a request header for sending on an HTTP transport. */
  public void writeRequest(Headers headers, String requestLine) throws IOException {
    //写入header
    if (state != STATE_IDLE) throw new IllegalStateException("state: " + state);
    //Okio中的sink，底层是socket使用的是okio优化
    sink.writeUtf8(requestLine).writeUtf8("\r\n");
    for (int i = 0, size = headers.size(); i < size; i++) {
      sink.writeUtf8(headers.name(i))
          .writeUtf8(": ")
          .writeUtf8(headers.value(i))
          .writeUtf8("\r\n");
    }
    sink.writeUtf8("\r\n");
    state = STATE_OPEN_REQUEST_BODY;
  }
```
可以看到这里其实没有什么复杂的逻辑，就是遍历Header，然后通过前一个过滤器建立的连接得到的Sink，来进行写操作，这也是为什么OkHttp依赖于Okio。这里还有一个可以注意的地方，这里最后将state变量赋值为了STATE_OPEN_REQUEST_BODY，其实会发现，随着方法的	进行，这个state变量会从上一个状态变为下一个状态，这里其实用到了**状态模式**的思想，虽然没有那么细致将每个状态分出来，但是状态模式的思想，状态的改变还是用到的。
##### 2.对于“Expect:100-continue”情况的处理
```
	Response.Builder responseBuilder = null;
    if (HttpMethod.permitsRequestBody(request.method()) && request.body() != null) {
      if ("100-continue".equalsIgnoreCase(request.header("Expect"))) {
        httpCodec.flushRequest();
        realChain.eventListener().responseHeadersStart(realChain.call());
        responseBuilder = httpCodec.readResponseHeaders(true);
      }
```
这里先说明一下是什么情况：
>当Header为Expect: 100-continue时，只发送请求头
>1. 发送一个请求, 包含一个Expect:100-continue, 询问Server使用愿意接受数据
>2. 接收到Server返回的100-continue应答以后, 才把数据POST给Server

所以对应注意几个点：
1.```Response.Builder responseBuilder = null;```首先构建了一个null的responseBuilder。
2.执行```httpCodec.flushRequest()```刷新请求。
3.执行```httpCodec.readResponseHeaders(true);```读取response的header信息，并返回一个responseBuilder赋值给responseBuilder。
这里看一下readResponseHeaders方法。
```
@Override public Response.Builder readResponseHeaders(boolean expectContinue) throws IOException {
    if (state != STATE_OPEN_REQUEST_BODY && state != STATE_READ_RESPONSE_HEADERS) {
      throw new IllegalStateException("state: " + state);
    }

    try {
      StatusLine statusLine = StatusLine.parse(readHeaderLine());
	//构建一个reponseBuilder
      Response.Builder responseBuilder = new Response.Builder()
          .protocol(statusLine.protocol)
          .code(statusLine.code)
          .message(statusLine.message)
          .headers(readHeaders());
	//如果得到的返回码是可以继续访问，返回null
      if (expectContinue && statusLine.code == HTTP_CONTINUE) {
        return null;
      }

      state = STATE_OPEN_RESPONSE_BODY;
	//不然返回构建出来的reponseBuilder
      return responseBuilder;
    } catch (EOFException e) {
      // Provide more context if the server ends the stream before sending a response.
      IOException exception = new IOException("unexpected end of stream on " + streamAllocation);
      exception.initCause(e);
      throw exception;
    }
  }
```
这里其实就看我标注的三处注释，可以看到得到Response的Header后，第一步：构建了一个ResponseBulder。第二步：通过返回的状态码判断是否请求可以继续进行（“Expect:100-continue”情况的处理），如果可以返回null.第三步：否则，也就是不可以，返回构建的ResponseBuilder。

所以综上就可以看出来，对于“Expect:100-continue”情况的处理总体为：
1.如果可以继续请求，则responseBuilder=null
2.如果不行，则responseBuilder不为空，并且为返回的Header

##### 3.写入请求体
```
if (responseBuilder == null) {
        //得到响应后，根据Resposne判断是否写入请求体
        // Write the request body if the "Expect: 100-continue" expectation was met.
        //写入请求体
        realChain.eventListener().requestBodyStart(realChain.call());
        long contentLength = request.body().contentLength();
        CountingSink requestBodyOut =
            new CountingSink(httpCodec.createRequestBody(request, contentLength));
        BufferedSink bufferedRequestBody = Okio.buffer(requestBodyOut);

        request.body().writeTo(bufferedRequestBody);
        bufferedRequestBody.close();
        //写入完成
        realChain.eventListener()
            .requestBodyEnd(realChain.call(), requestBodyOut.successfulCount);
      } else if (!connection.isMultiplexed()) {
        // If the "Expect: 100-continue" expectation wasn't met, prevent the HTTP/1 connection
        // from being reused. Otherwise we're still obligated to transmit the request body to
        // leave the connection in a consistent state.
        streamAllocation.noNewStreams();
      }
```
上面的步骤2看完后，这一步就很好理解了，如果可以继续请求，则Responsebuilder=null，执行if判断里的内容，可以看到就是对于请求体的写入操作，当然任然是使用Okio进行写入操作。
##### 4.构建响应头
```
//结束请求
    httpCodec.finishRequest();

    if (responseBuilder == null) {
      //得到响应头
      realChain.eventListener().responseHeadersStart(realChain.call());
      responseBuilder = httpCodec.readResponseHeaders(false);
    }

    Response response = responseBuilder
        .request(request)
        .handshake(streamAllocation.connection().handshake())
        .sentRequestAtMillis(sentRequestMillis)
        .receivedResponseAtMillis(System.currentTimeMillis())
        .build();

    realChain.eventListener()
        .responseHeadersEnd(realChain.call(), response);
```
延续上面的，当写入请求体后，当然就是得到响应了，由于这里的responseBuilder仍然为null，所以执行的还是我们上面步骤2分析过的方法```httpCodec.readResponseHeaders(false);```,这时再通过返回得到的responseBuilder构建携带有响应头的Reponse。
##### 5.构建响应体，返回响应
```
int code = response.code();
    if (forWebSocket && code == 101) {
      // Connection is upgrading, but we need to ensure interceptors see a non-null response body.
      response = response.newBuilder()
          .body(Util.EMPTY_RESPONSE)
          .build();
    } else {
      //构建响应体
      response = response.newBuilder()
          .body(httpCodec.openResponseBody(response))
          .build();
    }

    if ("close".equalsIgnoreCase(response.request().header("Connection"))
        || "close".equalsIgnoreCase(response.header("Connection"))) {
      streamAllocation.noNewStreams();
    }

    if ((code == 204 || code == 205) && response.body().contentLength() > 0) {
      throw new ProtocolException(
          "HTTP " + code + " had non-zero Content-Length: " + response.body().contentLength());
    }
    //返回响应
    return response;
```
剩下的其实就是对弈返回码的判断，对应正常的返回码的话，构建响应体到Response中，最后将Response返回。


终于---------------------------------------------------------------------------------->结束
>总结：
>历经5篇博客，初步把okHttp的过滤器全部发全部分析完了，期间有过想要放弃，因为真正看过源码的应该会明白我的感受吧。OkHttp其实从层面上来说给我的感觉相较于Volley更底层一些，级别类同于HttpURLConnection，将网络协议用代码进行实现，并层层优化，直到最后的Socket用了Okio进行替换。
>有时会有将Volley，retrofit，Okhttp进行比较优劣的，其实给我的感觉，Volley和Retrofit属于一个层面，OkHttp相较于前两个属于更深的层面，完全可以替换一下Volley底层执行网络协议的内核，替换为OkHttp，retrofit更不用说，底层就是okHttp，但是retrofit和volley相比哪，抛开okHttp这个因素，其实各有优劣，根据自己的需要吧，如果想要rxjava，耦合度极低，适合拓展，接口RESTful,当然retrofit欢迎你。
>通过看OkHttp的源码除了原理外，其实可以发现许多其他的东西：
1.首先发现了计算机网络的重要性，Http协议，准备后面入一本书，再回顾学习一下。
2.线程安全各种方式，各种数据结构。
3.设计模式，粗略回顾一下：建造者模式，责任链模式，策略模式...其实不用强行使用设计模式，其实主要是设计思想
4.面向接口编程，这个不用说，越看越重要。
5.方法的命名，其实我感觉挺有趣，也挺讲究的。
6.注释，其实和5差不多，基本上就是编程风格了。

