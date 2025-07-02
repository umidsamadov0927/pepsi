let btn2 = document.getElementById("btn");
let btn3 = document.getElementById("btn2");
let a = 0
let div = document.getElementById("div");
btn2.addEventListener("click", ()=>{
    if (a<100){
        a++
        div.innerText = a
    }else{
        alert("100dan utib bulmaydi")
    }
})
btn3.addEventListener("click", ()=>{
    if (a>0){
        a--
        div.innerText = a
    }else{
        alert("0dan pasga tushib bulmaydi")
    }
})