/* Hide top menu part with scroll */
$(window).on('scroll', function() {
    if ($(window).scrollTop() > 145) {
        $('.wp-contact-navbar').hide();
        if(!$('header').hasClass('homepage-header')){
            $('.header-fixed-margin').show();
            $('#wrap').css({'margin-top': '130px'});
        }
        $('header').addClass('fixed');
    } else {
        $('header').removeClass('fixed');
        if(!$('header').hasClass('homepage-header')){
            $('#wrap').css({'margin-top': '0px'});
            $('.header-fixed-margin').hide();
        }
        $('.wp-contact-navbar').show();
    }
});

/* Add modal "Add to Cart" window a to cart redirect */
odoo.define('theme_forestal.website_sale', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    require('web.dom_ready');
    var weContext = require("web_editor.context");
    require('website_sale.website_sale');

    $('.oe_website_sale #add_to_cart, .oe_website_sale #products_grid .a-submit').off('click').removeClass('a-submit').click(_.debounce(function (event) {
        var $form = $(this).closest('form');
        var quantity = parseFloat($form.find('input[name="add_qty"]').val() || 1);
        var product_id = parseInt($form.find('input[type="hidden"][name="product_id"], input[type="radio"][name="product_id"]:checked').first().val(),10);
        event.preventDefault();
        ajax.jsonRpc("/shop/modal", 'call', {
                'product_id': product_id,
                'kwargs': {
                   'context': _.extend({'quantity': quantity}, weContext.get())
                },
            }).then(function (modal) {
                var $modal = $(modal);

                $modal.find('img:first').attr("src", "/web/image/product.product/" + product_id + "/image_medium");

                // disable opacity on the <form> if currently active (in case the product is
                // not published), as it interferes with bs modals
                $form.addClass('css_options');

                $modal.appendTo($form)
                    .modal()
                    .on('hidden.bs.modal', function () {
                        $form.removeClass('css_options'); // possibly reactivate opacity (see above)
                        $(this).remove();
                    });

                $modal.on('click', '.a-submit', function (ev) {
                    var $a = $(this);
                    $form.ajaxSubmit({
                        url:  '/shop/cart/update_option',
                        data: {lang: weContext.get().lang},
                        success: function (quantity) {
                            if (!$a.hasClass('js_goto_shop')) {
                                window.location.replace("/shop/cart");
                            }
                            var $q = $(".my_cart_quantity");
                            $q.parent().parent().removeClass("hidden", !quantity);
                            $q.html(quantity).hide().fadeIn(600);
                        }
                    });
                    $modal.modal('hide');
                    ev.preventDefault();
                });

                $modal.on('click', '.css_attribute_color input', function (event) {
                    $modal.find('.css_attribute_color').removeClass("active");
                    $modal.find('.css_attribute_color:has(input:checked)').addClass("active");
                });

                $modal.on("click", "a.js_add, a.js_remove", function (event) {
                    event.preventDefault();
                    var $parent = $(this).parents('.js_product:first');
                    $parent.find("a.js_add, span.js_remove").toggleClass("hidden");
                    $parent.find("input.js_optional_same_quantity").val( $(this).hasClass("js_add") ? 1 : 0 );
                    $parent.find(".js_remove");
                });

                $modal.on("change", "input.js_quantity", function () {
                    var qty = parseFloat($(this).val());
                    if (qty === 1) {
                        $(".js_remove .js_items").addClass("hidden");
                        $(".js_remove .js_item").removeClass("hidden");
                    } else {
                        $(".js_remove .js_items").removeClass("hidden").text($(".js_remove .js_items:first").text().replace(/[0-9.,]+/, qty));
                        $(".js_remove .js_item").addClass("hidden");
                    }
                });

                $modal.find('input[name="add_qty"]').val(quantity).change();
                $('.js_add_cart_variants').each(function () {
                    $('input.js_variant_change, select.js_variant_change', this).first().trigger('change');
                    });

                    $modal.on("change", 'input[name="add_qty"]', function (event) {
                        var product_id = $($modal.find('span.oe_price[data-product-id]')).first().data('product-id');
                        var product_ids = [product_id];
                        var $products_dom = [];
                        $("ul.js_add_cart_variants[data-attribute_value_ids]").each(function(){
                            var $el = $(this);
                            $products_dom.push($el);
                            _.each($el.data("attribute_value_ids"), function (values) {
                                product_ids.push(values[0]);
                            });
                        });
                });
            });
        return false;
    }, 200, true));

    /* Set product length */
    $('.oe_website_sale').each(function () {
        var oe_website_sale = this;
        var $input_length = $("input[name='custom_length']").filter(':checked')
        var length = 0;

        $input_length.on('change', 'input:checked', function () {
                console.log('$input_length: ' + $(this).val())
                length = $(this).val();
            });

        $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
            var $ul = $(ev.target).closest('.js_add_cart_variants');
            var $parent = $ul.closest('.js_product');
            var $product_id = $parent.find('.product_id').first();
            var $input_radio = $parent.find("input.js_variant_change:radio, select.js_variant_change").filter(':checked')
            var id = $input_radio.val()

            console.log('$input_radio: ' + $input_radio.val())

            if(id == 'on'){
                console.log('$input_radio: ' + $input_radio.val())
                console.log('$input_length: ' + $input_length.val())
                console.log('$product_id: ' + $product_id.val())
                console.log('length: ' + length)
                $parent.removeClass("css_not_available");
                if(length != 0){
                    $parent.find("#add_to_cart").removeClass("disabled");
                }

            }
        });
    });
});
