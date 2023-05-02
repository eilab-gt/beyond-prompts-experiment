import React, {useEffect} from 'react';
import {
    Widget,
    addResponseMessage,
    toggleWidget,
    renderCustomComponent,
    toggleInputDisabled,
    setQuickButtons
} from 'react-chat-widget';
import io from 'socket.io-client';
import 'react-chat-widget/lib/styles.css';
import './Chatbox.css'


// Note: chatbot widget documentation at https://github.com/Wolox/react-chat-widget/issues/130

const Chatbox = (props) => {
    let options;

    useEffect(() => {
        addResponseMessage("Hello! I'm your Creative Wand.");
        toggleWidget();
        //toggleInputDisabled();
    }, []);

    useEffect(() => {
        const messageListener = (message) => {
            if (message['id'] === props.uuid) {
                addResponseMessage(message['message']);
                if ('options' in message) {
                    //dicts of label,value
                    setQuickButtons(message['options'])
                } else {
                    setQuickButtons([])
                }

            }
        };

        props.socket.on('message', messageListener);

        return () => {
            props.socket.off('message', messageListener);
        };
    }, [props.socket]);


    const handleNewUserMessage = async (newMessage) => {
        props.socket.emit('chat_message', {message: newMessage, code: props.code, id: props.uuid});
    };

    useEffect(() => {
        console.log("OP:" + options)
        if (!(options === undefined)) {
            setQuickButtons(options);
        }

    }, [options])

    const handleQuickButtonClicked = async (data) => {
        // remove all quick buttons until next time we need them
        setQuickButtons([])
        handleNewUserMessage(data)
        //setQuickButtons(buttons.filter(button => button.value !== data));
    };

    return (
        <div>
            <Widget
                handleNewUserMessage={handleNewUserMessage}
                resizable={true}
                title="Creative Wand"
                subtitle="Make a choice by clicking the buttons or saying the text in []."
                showTimeStamp={false}
                handleQuickButtonClicked={handleQuickButtonClicked}
            />
        </div>
    );
}

export default Chatbox;
  