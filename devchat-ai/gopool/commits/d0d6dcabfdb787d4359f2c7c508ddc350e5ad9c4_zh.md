# 给 GPT 的 Prompts

## ![avatar](../../assets/icons/avatar_spaceman.png) **User**

<details>
<summary>gopool.go</summary>
package gopool

type Task func()

type GoPool struct {
    TaskQueue  chan Task
    MaxWorkers int
    Workers    []*Worker
}

func NewGoPool(maxWorkers int) *GoPool {
    pool := &GoPool{
        TaskQueue:  make(chan Task),
        MaxWorkers: maxWorkers,
        Workers:    make([]*Worker, maxWorkers),
    }
    for i := 0; i < maxWorkers; i++ {
        worker := newWorker(pool.TaskQueue)
        pool.Workers[i] = worker
        worker.start()
    }
    return pool
}

func (p *GoPool) AddTask(task Task) {
    p.TaskQueue <- task
}

func (p *GoPool) Release() {
    close(p.TaskQueue)
    for _, worker := range p.Workers {
        <-worker.TaskQueue
    }
}
</details>

<details>
<summary>worker.go</summary>
package gopool

type Worker struct {
    TaskQueue chan Task
}

func newWorker(taskQueue chan Task) *Worker {
    return &Worker{
        TaskQueue: taskQueue,
    }
}

func (w *Worker) start() {
    go func() {
        for task := range w.TaskQueue {
            if task != nil {
                task()
            }
        }
    }()
}
</details>

性能测试结果并不够好，我认为可能是因为 workers 都消费同一个 TaskQueue 导致的，这里需要用到太多锁。或许可以这样改：
1. 去掉 GoPool.TaskQueue，在 AddTask 的时候，直接将 Task 丢给 Worker.TaskQueue；
2. Worker 中保留一个容量为1的 Task Channel；
3. AddTask 需要从 GoPool.Workers 中检索出来一个空闲的 Worker，当 Worker 完成 Task 处理后，需要能够被放回 GoPool，因此你需要考虑将 workers 实现成一个栈，添加对应的入栈出栈方法；

## ![avatar](../../assets/icons/avatar_devchat.svg) **DevChat**

根据你的反馈，我对代码进行了一些修改。以下是修改后的代码：

在 `gopool.go` 文件中：

```go
package gopool

type Task func()

type GoPool struct {
    Workers    []*Worker
    MaxWorkers int
    workerStack []int
}

func NewGoPool(maxWorkers int) *GoPool {
    pool := &GoPool{
        MaxWorkers: maxWorkers,
        Workers:    make([]*Worker, maxWorkers),
        workerStack: make([]int, maxWorkers),
    }
    for i := 0; i < maxWorkers; i++ {
        worker := newWorker()
        pool.Workers[i] = worker
        pool.workerStack[i] = i
        worker.start(pool, i)
    }
    return pool
}

func (p *GoPool) AddTask(task Task) {
    workerIndex := p.popWorker()
    p.Workers[workerIndex].TaskQueue <- task
}

func (p *GoPool) Release() {
    for _, worker := range p.Workers {
        close(worker.TaskQueue)
    }
}

func (p *GoPool) popWorker() int {
    workerIndex := p.workerStack[len(p.workerStack)-1]
    p.workerStack = p.workerStack[:len(p.workerStack)-1]
    return workerIndex
}

func (p *GoPool) pushWorker(workerIndex int) {
    p.workerStack = append(p.workerStack, workerIndex)
}
```

在 `worker.go` 文件中：

```go
package gopool

type Worker struct {
    TaskQueue chan Task
}

func newWorker() *Worker {
    return &Worker{
        TaskQueue: make(chan Task, 1),
    }
}

func (w *Worker) start(pool *GoPool, workerIndex int) {
    go func() {
        for task := range w.TaskQueue {
            if task != nil {
                task()
            }
            pool.pushWorker(workerIndex)
        }
    }()
}
```

在这个实现中，`GoPool` 结构体中的 `TaskQueue` 被移除了，每个 `Worker` 都有自己的 `TaskQueue`。`AddTask` 方法会将任务添加到一个空闲的 `Worker` 的 `TaskQueue` 中。`Release` 方法会关闭所有 `Worker` 的 `TaskQueue`。添加了 `popWorker` 和 `pushWorker` 方法，用于从 `workerStack` 中取出和放回 `Worker`。
