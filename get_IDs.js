async function f1() {
    const leagueID = window.location.href.split("/")[4];
    Array.from(document.getElementsByTagName("button")).filter(button => button.innerText === "Details")[0].click();
    members = parseInt(document.getElementsByTagName("span")[Array.from(document.getElementsByTagName("span")).map(x => x.innerText).findIndex((x) => x === leagueID) + 2].innerText, 10);
    for (let i = 0; i < Math.floor(members / 15); i++) {
        setTimeout(function timer() {
            Array.from(document.getElementsByTagName("button")).filter(button => button.innerText === "Show More")[0].click()
        }, i * 200);
    }
    return members;
}

const delay = ms => new Promise(res => setTimeout(res, ms));

async function f2() {
    ids = [];
    for (i = 2; i < members + 2; i++) {
        try {
            var id = document.getElementsByTagName("tr")[i].getElementsByTagName("a")[1].href.split("user/")[1];
            if (!isNaN(id)) {
                ids.push(parseInt(id));
            }
        } catch {
            // error will be caused by yourself as your profile link doesn't contain your user ID
        }
    }
    console.log(ids.join(", "));
}

f1();
console.log(members);
await delay(Math.ceil(members / 15) * 250);
f2();