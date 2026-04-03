---
title: "出现情形："
date: 2016-04-01 08:00:00 +0800
categories: ["读书笔记"]
source_name: "《HeadFrist-设计模式》读书笔记-——-策略模式"
---
定义了一个父类鸭子，定义的有叫，游方法，子类有：活鸭子，玩具鸭子等，这时想在父类鸭子中加上飞这个操作，这时会出现情况，活鸭子可以实现叫，飞，游方法，但是玩具鸭子只能实现叫，游，并不能**飞**。
### 思路进程：
1.**利用继承：**直接在父类中加上fly（）方法，这样需要在不同的子类中覆盖fly方法，活鸭子就可以飞，但是玩具鸭就不能飞。
缺点：
1）加个方法就需要在所有的子类中改变。
2）代码在子类中重复。不能飞的话，不能飞的子类都需要实现不能飞操作。
3）运行时的行为不容易改变。
4）很难知道所有鸭子的全部行为。

2.**利用接口：**将fly方法定义成接口，能飞的就实现这个接口的fly方法。
缺点：
子类需要重复实现接口方法。（1000个子类都需要实现一遍fly（）方法，但是fly仅仅fly。。）

### 类图：
![这里写图片描述](http://upload-images.jianshu.io/upload_images/7866586-ab29e373c95e00f6?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
可以看到，对于易变的fly和quack行为，抽出来以接口的形式定义，不同的fly方式和quack方式实现接口里的fly方法和quack方法，而Duck对象以组合的形式持有FlyBehavior和QuackBehavior接口，分别在performFly方法和performQuack方法中调用FlyBehavior.fly和QuackBehavior.quack方法。这样在不同的Duck类型中，可以动态的设置不同的fly和quack类型，但是调用的都是同样的performFly和performQuack方法。

### 代码实现：
父类Duck

```
public abstract class Duck {
    FlyBehavior mFlyBehavior;
    QuackBehavior mQuackBehavior;

    public abstract void display();

    public abstract void swim();

    public void performFly() {
        mFlyBehavior.fly();
    }

    public void performQuack() {
        mQuackBehavior.quack();
    }

    public void setmFlyBehavior(FlyBehavior mFlyBehavior) {
        this.mFlyBehavior = mFlyBehavior;
    }

    public void setmQuackBehavior(QuackBehavior mQuackBehavior) {
        this.mQuackBehavior = mQuackBehavior;
    }
	}
```

FlyBehavior
 

```
public interface FlyBehavior {
    public void fly();
	}
```

PlaneFly-飞的像飞机一样快

```
public class PlaneFly implements FlyBehavior {
    @Override
    public void fly() {
        Log.i("TAG", "fly by plane");
    }
	}
```

RocketFly-飞的像火箭一样快
 

```
public class RocketFly implements FlyBehavior {
    @Override
    public void fly() {
        Log.i("TAG", "fly by rocket");
    }
	}
```

QuackBehavior

```
public interface QuackBehavior {
    public void quack();
	}
```

BigQuack - 大声叫

```
public class BigQuack implements QuackBehavior {
    @Override
    public void quack() {
        Log.i("TAG", "Quack is big");
    }
	}
```

SmallQuack-小声叫

```
public class SmallQuack implements QuackBehavior {
    @Override
    public void quack() {
        Log.i("TAG", "quack is small");
    }
	}
```

StrategyActivity

```
public class StrategyActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.strategy_main);
        TopDuck topDuck = new TopDuck();
        test(topDuck,new RocketFly(),new BigQuack());

        SmallDuck smallDuck = new SmallDuck();
        test(smallDuck,new PlaneFly(),new SmallQuack());
    }

    private void test(Duck duck, FlyBehavior flyBehavior, QuackBehavior quackBehavior) {
        duck.display();
        duck.swim();
        duck.setmFlyBehavior(flyBehavior);
        duck.setmQuackBehavior(quackBehavior);
        duck.performFly();
        duck.performQuack();
    }
	}
```

待续...（对设计模式更深入理解后）