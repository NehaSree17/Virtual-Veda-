// Navigate to a new page
function gotonew(page) {
    window.location.href = page;
}

// Get and show IP address (for teacher) + initialize new class
async function getip() {
    const x = document.getElementById('ipadd');
    const y = await eel.getIP4()();
    x.innerHTML = y;
    eel.newclass();
}

// Get student name & IP, join class
function getnameandip() {
    const name = document.getElementById("studentname").value;
    const classip = document.getElementById("classip").value;

    if (name === "" || classip === "") {
        alert("Name and Class code are required", "error");
        window.location = "joinclass.html";
        return;
    }

    eel.joinclass(name, classip);
    window.location = "studentanalysis.html";
}

// Teacher not present (invalid code)
eel.expose(teachernotpresent);
function teachernotpresent() {
    window.location = "joinclass.html";
    alert("Class code is invalid, try contacting your teacher if this is a mistake.");
}

// Create initial table with headings
eel.expose(createtable);
function createtable() {
    const t = document.getElementById("studentvalues");
    const row = t.insertRow(-1);
    const cell1 = row.insertCell(0);
    const cell2 = row.insertCell(1);
    cell1.innerHTML = "<strong>Name of Student</strong>";
    cell2.innerHTML = "<strong>Attention</strong>";
}

// Alert and redirect student
eel.expose(alertstudent);
function alertstudent(message, page) {
    alert(message);
    window.location = page;
}

// Add user row to table
eel.expose(adduser);
function adduser(username) {
    const t = document.getElementById("studentvalues");
    const row = t.insertRow(-1);
    const cell1 = row.insertCell(0);
    const cell2 = row.insertCell(1);
    cell1.innerHTML = username;
    cell2.innerHTML = "0 %";
}

// Update attention value in table
eel.expose(appendattention);
function appendattention(username, attention) {
    const t = document.getElementById("studentvalues");
    const tr = t.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        const target = tr[i].getElementsByTagName("td")[0];
        if (target.innerText === username) {
            tr[i].getElementsByTagName("td")[1].innerHTML = attention;
        }
    }
}

// Render current attention value on student screen
eel.expose(render);
function render(att) {
    const y = document.getElementById("attlevel");
    y.innerHTML = att;
}

// Delete student from table
eel.expose(deletestudent);
function deletestudent(name) {
    const t = document.getElementById("studentvalues");
    const tr = t.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        const target = tr[i].getElementsByTagName("td")[0];
        if (target.innerText === name) {
            t.deleteRow(i);
            break;
        }
    }
}
