// Fictional classroom profiles; ages refer to 2026-10-13.
const peopleProfiles = [
  {name:'Lucía',paternal:'García',maternal:'López',age:12,ageWord:'doce',country:'España',nationality:'española',city:'Madrid',hobby:'leer y escuchar música',gender:'f'},
  {name:'Diego',paternal:'Martín',maternal:'Ruiz',age:13,ageWord:'trece',country:'México',nationality:'mexicano',city:'Ciudad de México',hobby:'jugar al fútbol y dibujar',gender:'m'},
  {name:'Ana',paternal:'Pérez',maternal:'Torres',age:11,ageWord:'once',country:'China',nationality:'china',city:'Shanghái',hobby:'bailar y estudiar español',gender:'f'}
];
function peopleQuestions(p,third=false){
  return [
    {label:'名字',question:third?'¿Cómo se llama?':'¿Cómo te llamas?',alternative:third?'¿Cuál es su nombre?':'¿Cuál es tu nombre?',answers:[`${third?'Se llama':'Me llamo'} ${p.name}.`,`${third?'Su':'Mi'} nombre es ${p.name}.`]},
    {label:'姓氏',question:third?'¿Cómo se apellida?':'¿Cómo te apellidas?',alternative:third?'¿Cuál es su apellido?':'¿Cuál es tu apellido?',answers:[`${third?'Se apellida':'Me apellido'} ${p.paternal} ${p.maternal}.`,`${third?'Sus':'Mis'} apellidos son ${p.paternal} ${p.maternal}.`]},
    {label:'父姓',question:third?'¿Cuál es su apellido paterno?':'¿Cuál es tu apellido paterno?',answers:[`${third?'Su':'Mi'} apellido paterno es ${p.paternal}.`]},
    {label:'母姓',question:third?'¿Cuál es su apellido materno?':'¿Cuál es tu apellido materno?',answers:[`${third?'Su':'Mi'} apellido materno es ${p.maternal}.`]},
    {label:'年龄',question:third?'¿Cuántos años tiene?':'¿Cuántos años tienes?',answers:[`${third?'Tiene':'Tengo'} ${p.ageWord} años.`,`${third?'Tiene':'Tengo'} ${p.age} años.`]},
    {label:'国家',question:third?'¿De qué país es?':'¿De dónde eres?',answers:[`${third?'Es':'Soy'} de ${p.country}.`]},
    {label:'国籍',question:third?'¿Cuál es su nacionalidad?':'¿Cuál es tu nacionalidad?',answers:[`${third?'Es':'Soy'} ${p.nationality}.`]},
    {label:'居住地',question:third?'¿Dónde vive?':'¿Dónde vives?',answers:[`${third?'Vive':'Vivo'} en ${p.city}.`]},
    {label:'爱好',question:third?'¿Cuáles son sus aficiones?':'¿Cuáles son tus aficiones?',answers:[`${third?'Sus':'Mis'} aficiones son ${p.hobby}.`]}
  ];
}
