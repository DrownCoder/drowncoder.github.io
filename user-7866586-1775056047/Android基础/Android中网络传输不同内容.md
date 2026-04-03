最近在实现向服务器发送数据，遇到一个小问题，Android中发送不同的数据内容的实现方式也不相同。下面解决了传递三种不同信息的三种方式。
1.传输键-值对（key-value）
2.传输自定义对象（Object）
3.传输自定义对象集合（List< Object >）

一、网络传输键值对（key-value）
Android中传递键值对我使用的方式是利用NameValuePair进行传输。这个应该比较基础，是比较传统的Android中网络传输的方式。
**要点：将你要传输的键值对利用NameValuePair封装成List集合进行传输。**
Android端：

```
    /**
     * 初始化发送的信息
     * @return
     */
    private List<NameValuePair> initMessage() {
        List<NameValuePair> message = new ArrayList<NameValuePair>();
        message.add(new BasicNameValuePair("name","张三"));
        message.add(new BasicNameValuePair("passwd", "112233"));
        return  message;
    }   
 /**
     * 网络传递键值对
     * @param content
     * @param url
     * @return
     */

    private static String HttpSentList(List<NameValuePair> content,String url){
        String result = null;
        HttpPost httpRequest = new HttpPost(url);
        try {
            HttpEntity httpEntity = new UrlEncodedFormEntity(content,"utf-8");
            httpRequest.setEntity(httpEntity);
            HttpClient httpClient = new DefaultHttpClient();
            HttpResponse httpResponse = httpClient.execute(httpRequest);
            int i = httpResponse.getStatusLine().getStatusCode();

            if(httpResponse.getStatusLine().getStatusCode() == HttpStatus.SC_OK){
                result = EntityUtils.toString(httpResponse.getEntity());
                return result;
            }else{
                //tv.setText("request error");
            }
        } catch (UnsupportedEncodingException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (ClientProtocolException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
        return result;
    }
```
**服务器端直接通过request对象拿对应key值的value对象即可。**
服务器端：

```
public void doPost(HttpServletRequest request, HttpServletResponse response)
			throws ServletException, IOException {
		//常规传参---键值对
		request.setCharacterEncoding("UTF-8");
		 String name = request.getParameter("name");
	     String passwd = request.getParameter("passwd");
			response.setContentType("text/html");
			PrintWriter out = response.getWriter();
			out
					.println("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">");
			out.println("<HTML>");
			out.println("  <HEAD><TITLE>A Servlet</TITLE></HEAD>");
			out.println("  <BODY>");
			out.print("    This is ");
			out.print("姓名："+name+"密码"+passwd);
			out.println(", using the GET method");
			out.println("  </BODY>");
			out.println("</HTML>");
			out.flush();
			out.close();
		System.out.print("姓名："+name+"密码"+passwd);

}
```

2.传输自定义对象（Object）
当网络中需要向服务器传输的是一个自定义对象，这时就不能用NameValuePair实现，需要用到java中学到的一个知识，使用**序列化对象**使用输入输出流进行传输序列化对象。
要点：
1.将自定义对象序列化
2.Android端和客户端需要都有这个序列化对象，且**类名和包名要相同**
Android端：

```
    /*
    初始化类对象信息
     */
    private Object initObjectMessage(){
        Book book = new Book();
        book.setName("疯狂Android讲义");
        book.setAuthor("李刚");
        return book;
    }
    /**
     * 网络传输对象流
     * @param obj
     * @param urlpos
     * @return
     */
    private static String HttpSentObject(Object obj,String urlpos){
        String line = "";
        URL url = null;
        ObjectOutputStream oos = null;
        try {
            url = new URL(urlpos);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setDoInput(true);
            connection.setDoOutput(true);
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(10000);
            connection.setRequestMethod("POST");
            oos = new ObjectOutputStream(connection.getOutputStream());
            oos.writeObject(obj);
            InputStreamReader read = new InputStreamReader(connection.getInputStream());
            BufferedReader br = new BufferedReader(read);
            while ((line = br.readLine()) != null) {
                Log.d("TAG", "line is " + line);
            }
            br.close();
            connection.disconnect();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {

        }
        return line;
    }
```
服务器端：
要点：
1.要有和Android端类名和包名相同的自定义对象。
2.利用输入输出流进行读写。

```
//对象流-----序列化对象
public void doPost(HttpServletRequest request, HttpServletResponse response)
			throws ServletException, IOException {
		ObjectInputStream ois = null;
	       try {
	             ois = new ObjectInputStream(request.getInputStream());
	             Book book = (Book) ois.readObject();
	             System.out.println("书名是： " + book.getName());
	             System.out.println("作者是： " + book.getAuthor());
	             PrintWriter out = response.getWriter();
	             out.print("success");
	             out.flush();
	             out.close();
	        } catch (Exception e) {
	             e.printStackTrace();
	        } finally {
	             ois.close();
	        }
	        }
```

3.传输自定义对象集合。（List< Object >）
当要传输自定义对象的集合时，利用的网络传输方式和二相同，因为
 oos.writeObject(obj);这个obj可以为List对象。但需要注意的一点是这其中我们使用的是ArrayList而不知List，至于List和ArrayList的区别自己到网上搜。
 Android端：
 

```
    private ArrayList<Object> initListObjMessage(){
        ArrayList<Object> list = new ArrayList<Object>();
        Book book1 = new Book();
        book1.setName("疯狂Android讲义");
        book1.setAuthor("李刚");
        Book book2= new Book();
        book2.setName("深入理解Android");
        book2.setAuthor("某某");
        list.add(book1);
        list.add(book2);
        return  list;
    }
 private static String HttpSentListObj(ArrayList<Object> obj, String urlpos){
        String line = "";
        URL url = null;
        ObjectOutputStream oos = null;
        try {
            url = new URL(urlpos);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setDoInput(true);
            connection.setDoOutput(true);
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(10000);
            connection.setRequestMethod("POST");
            oos = new ObjectOutputStream(connection.getOutputStream());
            oos.writeObject(obj);
            InputStreamReader read = new InputStreamReader(connection.getInputStream());
            BufferedReader br = new BufferedReader(read);
            while ((line = br.readLine()) != null) {
                Log.d("TAG", "line is " + line);
            }
            br.close();
            connection.disconnect();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {

        }
        return line;
    }
```
服务器端：
和二基本相同
	

```
public void doPost(HttpServletRequest request, HttpServletResponse response)
			throws ServletException, IOException {
//对象集合
		ObjectInputStream ois = null;
	       try {
	             ois = new ObjectInputStream(request.getInputStream());
	             List<Book> list = (List<Book>) ois.readObject();
	             System.out.println("书名是： " + list.get(0).getName());
	             System.out.println("作者是： " + list.get(0).getAuthor());
	             System.out.println("书名是： " + list.get(1).getName());
	             System.out.println("作者是： " + list.get(1).getAuthor());
	             PrintWriter out = response.getWriter();
	             out.print("success");
	             out.flush();
	             out.close();
	        } catch (Exception e) {
	             e.printStackTrace();
	        } finally {
	             ois.close();
	        }
	}
```

基本就这些了，算是一种总结吧。
