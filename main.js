function gotonew(p)
    {
    window.location = p;
    }

async function getip()
    {
    var x = document.getElementById('ipadd');
    let y = await eel.getIP4()()
    x.innerHTML= y
    eel.newclass()
    }

function getnameandip(){
    var name = document.getElementById("studentname").value;
    var classip = document.getElementById("classip").value;
    if(name=="" || classip ==""){
          alert("Name and Class code are required","error");
          window.location = "joinclass.html";
          return;
    }

    eel.joinclass(name,classip);
    window.location = "studentanalysis.html";
}
eel.expose(teachernotpresent);
function teachernotpresent(){
    window.location = "joinclass.html";
    alert("Class code is invalid, try contacting your teacher if this is a mistake.");

}
eel.expose(createtable);
function createtable(){
    console.log("gotit")
    var t= document.getElementById("studentvalues");
    var row = t.insertRow(-1);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    cell1.innerHTML = "<strong>Name of Student<strong>";
    cell2.innerHTML = "<strong>Attention<strong>";

}
eel.expose(alertstudent);
function alertstudent(m, h){
    alert(m)
    window.location = h;
}
eel.expose(adduser);
function adduser(username){
    var t= document.getElementById("studentvalues");
    var row = t.insertRow(-1);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    cell1.innerHTML = username
    cell2.innerHTML = "0 %";
}

eel.expose(appendattention);
function appendattention(username, attention){
    var t= document.getElementById("studentvalues");
    var tr = t.getElementsByTagName("tr");
    for (var i=1; i< tr.length; i++){
        target= tr[i].getElementsByTagName("td")[0]
        if (target.innerText ==username){
            tr[i].getElementsByTagName("td")[1].innerHTML= attention
            }
        }

}

eel.expose(render);
function render(att){
    var y= document.getElementById("attlevel");
    y.innerHTML= att;

}


eel.expose(deletestudent);
function deletestudent(name){
 var t= document.getElementById("studentvalues");
    var tr = t.getElementsByTagName("tr");
    for (var i=1; i< tr.length; i++){
        target= tr[i].getElementsByTagName("td")[0]
        if (target.innerText ==name){
            t.deleteRow(i)
            }
        }


}