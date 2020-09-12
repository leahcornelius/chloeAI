function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; } class App extends React.PureComponent {
  constructor(...args) {
    super(...args); _defineProperty(this, "state",

      {
        chat: []
      });
    _defineProperty(this, "saveMsg",


      msg => this.setState({
        chat: [
          ...this.state.chat,
          { message: msg, bot: false }]
      }));
    _defineProperty(this, "botMsg",
      botmsg => this.setState({
        chat: [
          ...this.state.chat,
          { message: botmsg, bot: true }]
      }));
  }


  render() {
    return (
      React.createElement("section", { className: "hero is-fullheight" },

        React.createElement("div", { className: "hero-head" },
          React.createElement("header", { className: "hero is-link is-bold" },
            React.createElement("div", { className: "hero-body" },
              React.createElement("div", { className: "container" },
                React.createElement("p", { className: "title" }, "Chloe AI"),


                React.createElement("p", { className: "subtitle" }, "Created by Leo Cornelius (2020)"))))),







        React.createElement("div", { className: "hero-body" },
          React.createElement(Messages, { chat: this.state.chat })),


        React.createElement("div", { className: "hero-foot" },
          React.createElement("footer", { className: "section is-small" },
            React.createElement(Chat, { saveMsg: this.saveMsg, botMsg: this.botMsg })))));




  }
}

const Chat = ({ saveMsg, botMsg }) =>
  React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      saveMsg(e.target.elements.userInput.value);
      msg = e.target.elements.userInput.value;
      e.target.reset();
      get_response(msg, botMsg);
    }
  },
    React.createElement("div", { className: "field has-addons" },
      React.createElement("div", { className: "control is-expanded" },
        React.createElement("input", { className: "input", name: "userInput", type: "text", placeholder: "Type your message" })),

      React.createElement("div", { className: "control" },
        React.createElement("button", { className: "button is-info" }, "Send"))));


function get_response(userMsg, bm) {
  console.log("User >>> " + userMsg);
  fetch('http://192.168.1.251:5000/get_response/' + userMsg)
    //.then(response => handleErrors(response, bm))
    .then(response => response.text())
    .then(response => {
      console.log(response);
      bm(response);
    })
    .catch(error => console.log(error))
}

function handleErrors(response, bm) {
  if (!response.ok) {
    error = response.statusText
    bm("Sorry :/ something went wrong.");
    bm("Error: " + error);
    bm("Please message Leo and give him this!");
    throw Error("Something went wrong. Error: " + error);
  }
  return response;
}



const Messages = ({ chat }) =>
  React.createElement("div", { style: { heigth: '100%', width: '100%' } },
    chat.map((m, i) => {
      const msgClass = m.bot;
      return (
        React.createElement("p", { style: { padding: '.25em', textAlign: msgClass ? 'left' : 'right', overflowWrap: 'normal' } },
          React.createElement("span", { key: i, className: `tag is-medium ${msgClass ? 'is-success' : 'is-info'}` }, m.message)));

    }));




ReactDOM.render(React.createElement(App, null), document.getElementById('root'));