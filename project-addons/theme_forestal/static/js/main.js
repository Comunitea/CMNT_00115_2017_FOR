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
        var product_uom_unit = parseFloat($form.find('input[name="product_uom_unit"]').val() || 1);
        var product_id = parseInt($form.find('input[type="hidden"][name="product_id"], input[type="radio"][name="product_id"]:checked').first().val(),10);
        var length = $("input[name='custom_length']").val() || 0
        event.preventDefault();
        ajax.jsonRpc("/shop/modal", 'call', {
                'product_id': product_id,
                'context': {'product_length': length, 'product_uom_unit': product_uom_unit,},
                'kwargs': {
                   'context': _.extend({'quantity': quantity,}, weContext.get())
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
                        data: {lang: weContext.get().lang, product_length: length,},
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

    $('.oe_website_sale').on('keyup', "label.control-label > input[name='custom_length'].active", function (ev) {
        var $add_button = $("#add_to_cart");
        var length = $("input[name='custom_length']").val();

        if (length.length == 0) {
            $add_button.parent().addClass("css_not_available");
            $add_button.addClass("disabled");
        } else {
            $add_button.parent().removeClass("css_not_available");
            $add_button.removeClass("disabled");
        }

    });

    $('.oe_website_sale').on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {

        var $ul = $(ev.target).closest('.js_add_cart_variants');
        var $parent = $ul.closest('.js_product');
        var custom_active = false;        

        $parent.find('input.js_variant_change:checked').each(function () {
            if($(this).siblings().last().is('input')) {
                custom_active = true;
            }
        });

        $parent.find('option[value="'+ $(this).val()+'"]').each(function () {
            if ($(this).attr("name") == 'custom_option') {
                custom_active = true;
            }
        });

        var input_length = $("input[name='custom_length']");

        function masive_toogling() {

            input_length.toggleClass('hidden form-control mt16', !custom_active);
            input_length.toggleClass('active form-control mt16', custom_active);
            
            if (custom_active == true) {
                input_length.trigger('keyup');
            } else {
                input_length.val(false);
            }
        }
        
        masive_toogling();
        
    });

    var clickwatch = (function(){
        var timer = 0;
        return function(callback, ms){
          clearTimeout(timer);
          timer = setTimeout(callback, ms);
        };
    })();

    $('.oe_website_sale').off('change', ".oe_cart input.js_quantity[data-product-id]").on("change", ".oe_cart input.js_quantity[data-product-id]", function () {
        var $input = $(this);
        if ($input.data('update_change') || $('body').hasClass('editor_enable')) {
            return;
        }
        var value = parseInt($input.val() || 0, 10);
        if (isNaN(value)) {
            value = 1;
        }
        var $dom = $(this).closest('tr');
        var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
        var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
        var line_id = parseInt($input.data('line-id'),10);
        var product_ids = [parseInt($input.data('product-id'),10)];
        clickwatch(function(){
        $dom_optional.each(function(){
            $(this).find('.js_quantity').text(value);
            product_ids.push($(this).find('span[data-product-id]').data('product-id'));
        });
        
        $input.data('update_change', true);

        ajax.jsonRpc("/shop/cart/update_json", 'call', {
            'line_id': line_id,
            'product_id': parseInt($input.data('product-id'), 10),
            'set_qty': value,
        }).then(function (data) {
            
            $input.data('update_change', false);
            var check_value = parseInt($input.val() || 0, 10);
            if (isNaN(check_value)) {
                check_value = 1;
            }
            if (value !== check_value) {
                $input.trigger('change');
                return;
            }
            var $q = $(".my_cart_quantity");
            
            if (data.cart_quantity) {
                $q.parents('li:first').removeClass("hidden");
            }
            else {
                $q.parents('li:first').addClass("hidden");
                $('a[href*="/shop/checkout"]').addClass("hidden");
            }

            $q.html(data.cart_quantity).hide().fadeIn(600);
            $input.val(data.quantity);
            $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);

            $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();

            if (data.warning) {
                var cart_alert = $('.oe_cart').parent().find('#data_warning');
                if (cart_alert.length === 0) {
                    $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">'+
                            '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
                }
                else {
                    cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
                }
                $input.val(data.quantity);
            }
        });
        }, 500);
    });

    // hack to add and remove from cart with json
    $('.oe_website_sale').off('click', 'a.js_add_cart_json').on('click', 'a.js_add_cart_json', function (ev) {
        if ($('body').hasClass('editor_enable')) {
            return;
        }
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.parent().find("input");
        var product_id = +$input.closest('*:has(input[name="product_id"])').find('input[name="product_id"]').val();
        var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || Infinity);
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val() || 0, 10);
        var new_qty = quantity > min ? (quantity < max ? quantity : max) : min;

        // If there is any product with custom length
        var is_custom_length = $link.hasClass("product_uom_unit_add");
        if (is_custom_length) {
            $('input[data-line-id="'+$input.data("line-id")+'"]').val(new_qty).change();
            return false;
        }        

        // if they are more of one input for this product (eg: option modal)
        $('input[name="'+$input.attr("name")+'"]').add($input).filter(function () {
            var $prod = $(this).closest('*:has(input[name="product_id"])');
            return !$prod.length || +$prod.find('input[name="product_id"]').val() === product_id;
        }).val(new_qty).change();
        return false;
    });

});