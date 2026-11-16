var express = require('express');
var app = express();

const path = require('path');

const bodyParser = require('body-parser');
const fileUpload = require('express-fileupload');
const sanitizer = require('sanitize')(); //var name = sanitizer.value(req.name, 'string');

const middlewares = [
  bodyParser.urlencoded({extended: true}),
  express.static('public'),
  fileUpload(
    //useTempFiles : true,
    //tempFileDir : '/tmp/'
  ),
];

const routes = require('./routes/routes');
const formRoutes = require('./routes/formRoutes');
const refreshRoutes = require('./routes/refreshRoutes');

app.set('view engine', 'ejs')

app.use(middlewares);

app.use('/', routes);
app.use('/go/', formRoutes);
app.use('/', refreshRoutes);

const PORT = 3000;
const HOST = '0.0.0.0'; // or '127.0.0.1' if you only need local access

app.use(function(req, res, next){
  //questa va fatta piu' completa, dividendo i vari errori
  res.status(404).render('generic_error.ejs');
});

app.listen(PORT, HOST, () => {
  console.log(`App listening at http://${HOST}:${PORT}`);
});

