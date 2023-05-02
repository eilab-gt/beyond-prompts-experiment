var React = require('react');

const HelpText = (props) => {
    return (
        <div>
            <a
                href="https://docs.google.com/document/d/1TDORUZlDuw9En_y77YTj7QZrDqX5EKABqiyjn0VFCwU/edit?usp=sharing"
                target="_blank"
            >Click here for the instructions.</a>
            <p>I'm your Creative Wand, here to work together on writing a story with you.</p>
            <p>You will see a list of actions available to you.</p>
            <p>Tell me what you wish to do by typing in the word in the bracket.</p>
            <p>Once you selected an action, I will further guide you through each of it.</p>
            <p>Enjoy the collaborative experience!</p>
        </div>

    );
}

export default HelpText;