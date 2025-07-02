let exit = document.getElementById("exit_btn");
let modal = document.querySelector('#modall');
let outBtn = document.getElementById("btn");
let lorem = document.querySelector('#lorem');
let txt = document.querySelector('#text');
let new2 = document.querySelector('#neww');
let lorem2 = lorem.value
outBtn.addEventListener("click", () => {
    modal.style.display = "block";
    txt.innerText = lorem.textContent;
})
exit.addEventListener("click", () => {
    modal.style.display = "none";

})