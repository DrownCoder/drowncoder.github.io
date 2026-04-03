---
title: "Android-Service、Activity、BroadcastReceiver简单使用"
date: 2017-09-26 00:27:59+08:00
categories: ["Android基础"]
source_name: "Android-Service、Activity、BroadcastReceiver简单使用"
jianshu_views: 889
jianshu_url: "https://www.jianshu.com/p/42b450f47e08"
---
最近在项目要用到一个**:提交->审核->审核通过**流程。
对应的我就想到要使用Activity与Service通过BroadcastReceiver的简单通信，完成后简单总结一下。

**实现思想：**
1.简单的Activity，当点击提交按钮时，开启一个后台Service用户执行网络通信。
2.后台Service，新建一个线程，线程中用一个死循环用户访问服务器通过情况，当后台服务器通过审核，跳出循环，发送完成的广播，线程执行结束。
3.广播，当Activity接收到审核通过的广播，更新UI显示审核通过。

**知识要点：**
1.Android中Service的使用。
2.Android中Activity与Service的通信方式。
3.BroadcastReceiver的两种注册方式。

Android使用Service的步骤：
一、重写Service

```
package com.example.service;

import com.example.HttpTools.WebAccessTools;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;

public class HttpService extends Service {
	private ServiceBind myBind = new ServiceBind();
	private int result=0;
	@Override
	/**
	*必须要重写的方法，用于和Activity通过bind通信
	*/
	public IBinder onBind(Intent arg0) {
		// TODO Auto-generated method stub
		return myBind;
	}
	public class ServiceBind extends Binder{
		public int getresult(){
			return result;
		}
	}
	@Override
	public void onCreate() {
		// TODO Auto-generated method stub
		new Thread(new 
				Runnable() {
					
					@Override
					public void run() {
						// TODO Auto-generated method stub
						HttpCheck();
						
					}
/*
*死循环，访问服务器，对服务器返回的数据进行判断，当判断通过的时候向Activity发送广播，跳出循环
*/
					private void HttpCheck() {
						// TODO Auto-generated method stub
						while(true){
							String url = "http://192.168.139.1/check.php";
							String res = WebAccessTools.getWebcontent(url);
							if(res.equals("1")){
								 Intent intent = new Intent();
							     intent.setAction("com.example.CHECKED");
							     sendBroadcast(intent);
								result = 1;
								break;
							}
							try {
								Thread.sleep(10000);
							} catch (InterruptedException e) {
								// TODO Auto-generated catch block
								e.printStackTrace();
							}
						}
					}
				}).start();
		super.onCreate();
	}

}

```
二、Activity中启动Service。

```
package com.example.servicedemo;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.TextView;

import com.example.service.HttpService;

public class MainActivity extends Activity implements OnClickListener{
	private Button submit;
	private TextView  checking;
	private TextView checked;
	private BroadcastReceiver mReceiver;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		initView();
		initEvent();
	}
	/*
	 *事件处理
	 */
	private void initEvent() {
		// TODO Auto-generated method stub
		submit.setOnClickListener(this);
	}
	/*
	 * 初始化组件
	 */
	private void initView() {
		// TODO Auto-generated method stub
		submit = (Button) findViewById(R.id.submit);
		checking = (TextView) findViewById(R.id.checking);
		checked = (TextView) findViewById(R.id.checked);
		/*
		*注册广播，当接收到审核通过的时候更新UI
		*/
		mReceiver = new BroadcastReceiver() {
			
			@Override
			public void onReceive(Context arg0, Intent arg1) {
				// TODO Auto-generated method stub
				checking.setVisibility(View.GONE);
				checked.setVisibility(View.VISIBLE);
			}
		};
		/*
		*广播接收器，动态注册广播，不需要在AndroidManifest.xml注册Receiver
		*/
		IntentFilter filter = new IntentFilter("com.example.CHECKED");
		this.registerReceiver(mReceiver, filter);
	}
	@Override
	public void onClick(View view) {
		// TODO Auto-generated method stub'
		checking.setVisibility(View.VISIBLE);
		Intent bindIntent  = new Intent(MainActivity.this,HttpService.class);
		startService(bindIntent);//开启广播
	}
}
WebAccessTools.java

```
package com.example.HttpTools;
import org.apache.http.HttpResponse;
import org.apache.http.HttpStatus;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.params.BasicHttpParams;
import org.apache.http.params.HttpConnectionParams;
import org.apache.http.params.HttpParams;
import org.apache.http.util.EntityUtils;

import android.content.Context;
import android.widget.Toast;

public class WebAccessTools {
      
    /** 
     * 当前的Context上下文对象 
     */  
    private static Context context;  
    /** 
     * 构造一个网站访问工具类 
     * @param context 记录当前Activity中的Context上下文对象 
     */  
    public WebAccessTools(Context context) {  
        this.context = context;  
    }  
      
    /** 
     * 根据给定的url地址访问网络，得到响应内容(这里为GET方式访问) 
     * @param url 指定的url地址 
     * @return web服务器响应的内容，为<code>String</code>类型，当访问失败时，返回为null 
     */  


	public static String getWebcontent(String url) {
        //创建一个http请求对象  
        HttpGet request = new HttpGet(url);  
        //创建HttpParams以用来设置HTTP参数  
        HttpParams params=new BasicHttpParams();  
        //设置连接超时或响应超时  
        HttpConnectionParams.setConnectionTimeout(params,15000);
        HttpConnectionParams.setSoTimeout(params, 15000);  
        //创建一个网络访问处理对象  
        HttpClient httpClient = new DefaultHttpClient(params);  
        try{  
            //执行请求参数项  
            HttpResponse response = httpClient.execute(request);  
            //判断是否请求成功  
            if(response.getStatusLine().getStatusCode() == HttpStatus.SC_OK) {  
                //获得响应信息  
                String content = EntityUtils.toString(response.getEntity(), "UTF-8"); //防止乱码 
                return content;  
            } else {  
                //网连接失败，使用Toast显示提示信息  
                Toast.makeText(context, "网络访问失败，请检查您机器的联网设备!", Toast.LENGTH_LONG).show();  
            }  
              
        }catch(Exception e) {  
            e.printStackTrace();  
        } finally {  
            //释放网络连接资源  
            httpClient.getConnectionManager().shutdown();  
        }  
        return null;  
	}  
} 
```

```
check.php

```
<?php
echo 0; //当换成echo 1;时更新UI
?>
```
总结：这次算是简单的接触Service和BroadcastReceiver对象。
Service与Activity通信有两种方式，第一种就是这次使用的广播BroadcastReceiver，适合数据更新。第二种是试用BindService的方式开启广播，然后通过bind通信，但是只能在Activity与SerVice连接的时候进行通信，有一定局限性。
BroadcastRecevier的注册方式有两种：
一、动态注册：

```
//注册广播接收器（动态注册）  
        IntentFilter filter = new IntentFilter(); 
        filter.addAction("ABC"); 
        this.registerReceiver(receiver, filter);  
```
二、静态注册：
也就是在AndroidManifest.xml中注册

```
 <receiver android:name="MyBroadcastReciever"> 
            <intent-filter> 
                <action android:name="ABC"></action> 
            </intent-filter> 
        </receiver> 
```


