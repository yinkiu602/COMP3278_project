$(document).ready(()=>{
    fetch("/fetch_all").then(temp => {
        temp.json().then(result => {
            console.log(result)
            var course = []
            for (i of result) {
                for (let j = parseInt(i[1]); j < parseInt(i[2]); j++) {
                    document.getElementById((j + "_" + i[0])).innerHTML = (i[3] + "<br>" + i[4])
                    let isFound = course.some(element => {
                        if (element == i[3]) {
                            return true;
                        }
                        return false;
                    });
                    if (isFound) {
                        document.getElementById((j + "_" + i[0])).setAttribute('class', `c${course.indexOf(i[3])}`)
                    } else {
                        course.push(i[3])
                        document.getElementById((j + "_" + i[0])).setAttribute('class', `c${course.indexOf(i[3])}`)
                    }
                }
            }
        })
    })
    document.getElementById("class_table")
})